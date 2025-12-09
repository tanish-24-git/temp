"""Preprocessing API Routes

Endpoints for document chunking and preprocessing.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID
from datetime import datetime
import logging

from ...database import get_db
from ...models.submission import Submission
from ...models.content_chunk import ContentChunk
from ...schemas.content_chunk import (
    PreprocessingRequest,
    PreprocessingResponse,
    ChunkListResponse,
    ContentChunkResponse
)
from ...services.preprocessing_service import PreprocessingService
from ...services.content_retrieval_service import ContentRetrievalService

router = APIRouter(prefix="/api/preprocessing", tags=["preprocessing"])
logger = logging.getLogger(__name__)


@router.post("/{submission_id}", response_model=PreprocessingResponse)
async def preprocess_submission(
    submission_id: UUID,
    request: PreprocessingRequest = PreprocessingRequest(),
    db: Session = Depends(get_db)
):
    """
    Preprocess a submission by chunking its content.
    
    **Process**:
    1. Validates submission exists
    2. Skips if already preprocessed
    3. Parses document based on content_type
    4. Creates chunks with metadata
    5. Stores chunks in database
    
    **Supported formats**: PDF, DOCX, HTML, Markdown
    """
    try:
        # Check submission exists
        submission = db.query(Submission).filter_by(id=submission_id).first()
        if not submission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Submission {submission_id} not found"
            )
        
        # Check if already preprocessed
        if submission.status == "preprocessed":
            chunk_count = db.query(ContentChunk).filter_by(
                submission_id=submission_id
            ).count()
            
            return PreprocessingResponse(
                success=True,
                submission_id=submission_id,
                chunks_created=chunk_count,
                status=submission.status,
                message="Submission already preprocessed"
            )
        
        # Run preprocessing
        service = PreprocessingService(db)
        chunks_created = await service.preprocess_submission(
            submission_id=submission_id,
            chunk_size=request.chunk_size,
            overlap=request.overlap
        )
        
        # Refresh submission to get updated status
        db.refresh(submission)
        
        logger.info(f"Preprocessing complete: {chunks_created} chunks created")
        
        return PreprocessingResponse(
            success=True,
            submission_id=submission_id,
            chunks_created=chunks_created,
            status=submission.status,
            message=f"Successfully created {chunks_created} chunks"
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Preprocessing failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Preprocessing failed: {str(e)}"
        )


@router.get("/{submission_id}/chunks", response_model=ChunkListResponse)
async def get_submission_chunks(
    submission_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Retrieve all chunks for a submission.
    
    **Unified Access**:
    - Returns real chunks if submission is preprocessed
    - Returns synthetic chunk if submission is legacy/unpreprocessed
    - Ensures frontend can always display "chunk" content
    """
    submission = db.query(Submission).filter_by(id=submission_id).first()
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Submission {submission_id} not found"
        )
    
    # Use consolidated retrieval service
    service = ContentRetrievalService(db)
    chunk_dtos = service.get_analyzable_content(submission_id, include_metadata=True)
    
    # helper to get timestamp (real or fallback)
    base_time = submission.submitted_at or datetime.utcnow()
    
    return ChunkListResponse(
        submission_id=submission_id,
        submission_title=submission.title,
        submission_status=submission.status,
        total_chunks=len(chunk_dtos),
        chunks=[
            ContentChunkResponse(
                id=c.id,
                submission_id=submission_id,
                chunk_index=c.chunk_index,
                text=c.text,
                token_count=c.token_count,
                # Ensure metadata is compatible
                metadata=c.metadata,
                created_at=base_time
            )
            for c in chunk_dtos
        ]
    )


@router.get("/{submission_id}/status")
async def get_preprocessing_status(
    submission_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get preprocessing status for a submission.
    
    **Statuses**:
    - `uploaded`: Not yet preprocessed
    - `preprocessing`: Currently chunking
    - `preprocessed`: Ready for analysis
    - `analyzing`: Compliance check running
    - `analyzed`: Analysis complete
    - `failed`: Error occurred
    """
    submission = db.query(Submission).filter_by(id=submission_id).first()
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Submission {submission_id} not found"
        )
    
    service = ContentRetrievalService(db)
    is_chunked = service.is_chunked(submission_id)
    chunk_count = service.get_chunk_count(submission_id)
    
    return {
        "submission_id": submission_id,
        "status": submission.status,
        "is_chunked": is_chunked,
        "chunk_count": chunk_count,
        "content_type": submission.content_type
    }


@router.delete("/{submission_id}/chunks")
async def delete_submission_chunks(
    submission_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Delete all chunks for a submission.
    
    **Use case**: Re-preprocess with different chunk parameters
    
    **Effect**: Resets submission status to `uploaded`
    """
    submission = db.query(Submission).filter_by(id=submission_id).first()
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Submission {submission_id} not found"
        )
    
    service = PreprocessingService(db)
    deleted_count = service.delete_chunks(submission_id)
    
    return {
        "success": True,
        "submission_id": submission_id,
        "chunks_deleted": deleted_count,
        "new_status": submission.status
    }
