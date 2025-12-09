"""Onboarding Service

Orchestrates user onboarding flow with intelligent rule generation.

Workflow:
1. Accept user context (industry, brand, scope)
2. Search for industry regulations (web search + RAG fallback)
3. Use Ollama to extract structured rules from search results
4. Store rules in database with metadata
5. Return onboarding summary
"""

import logging
from typing import List, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session

from ..models.user_config import UserConfig
from ..models.rule import Rule
from .web_search_service import web_search_service
from .ollama_service import ollama_service

logger = logging.getLogger(__name__)


class OnboardingService:
    """
    Generate initial compliance rules from user context.
    
    Creates personalized rule sets based on:
    - Industry (insurance, healthcare, etc.)
    - Analysis scope (regulatory, brand, seo, qualitative)
    - Region (defaults to India)
    """
    
    async def generate_rules_from_onboarding(
        self,
        user_id: UUID,
        industry: str,
        brand_name: str,
        analysis_scope: List[str],
        db: Session,
        region: str = "India"
    ) -> Dict[str, Any]:
        """
        Generate compliance rules from user onboarding data.
        
        Args:
            user_id: User UUID
            industry: Industry name (e.g., "insurance", "healthcare")
            brand_name: Company/brand name
            analysis_scope: Selected categories (e.g., ["regulatory", "brand", "seo"])
            db: Database session
            region: Geographic region for regulations
            
        Returns:
            {
                "rules_generated": 7,
                "by_category": {"irdai": 5, "brand": 3, "seo": 2},
                "sources_used": ["serper", "rag_fallback"]
            }
        """
        logger.info(f"Starting onboarding for user {user_id}, industry: {industry}")
        
        # Track sources used
        sources_used = []
        rules_by_category = {}
        all_rules = []
        
        # Step 1: Search for regulations (with RAG fallback)
        if "regulatory" in analysis_scope or "irdai" in analysis_scope:
            logger.info(f"Searching regulations for {industry}")
            search_results = await web_search_service.search_regulations(
                industry=industry,
                region=region,
                max_results=10
            )
            
            if search_results:
                source = search_results[0].get("source", "rag_fallback")
                sources_used.append(source)
                
                # Generate rules from search results
                regulatory_rules = await ollama_service.generate_rules_from_context(
                    search_results=search_results,
                    industry=industry,
                    scope="regulatory"
                )
                
                all_rules.extend(regulatory_rules)
                rules_by_category["irdai"] = len(regulatory_rules)
        
        # Step 2: Generate brand guidelines (if in scope)
        if "brand" in analysis_scope:
            logger.info("Searching brand guidelines best practices")
            brand_results = await web_search_service.search_brand_guidelines(
                industry=industry,
                topics=["tone", "terminology", "visuals"],
                max_results=5
            )
            
            if brand_results:
                brand_rules = await ollama_service.generate_rules_from_context(
                    search_results=brand_results,
                    industry=industry,
                    scope="brand"
                )
                
                all_rules.extend(brand_rules)
                rules_by_category["brand"] = len(brand_rules)
        
        # Step 3: SEO rules (always included, industry-agnostic)
        if "seo" in analysis_scope:
            logger.info("Generating SEO rules")
            # Use RAG fallback for SEO (universal best practices)
            from .compliance_knowledge_base import SEO_KNOWLEDGE
            
            seo_rules = await ollama_service.generate_rules_from_context(
                search_results=SEO_KNOWLEDGE,
                industry=industry,
                scope="seo"
            )
            
            all_rules.extend(seo_rules)
            rules_by_category["seo"] = len(seo_rules)
        
        # Step 4: Store rules in database
        for rule_data in all_rules:
            rule = Rule(
                category=rule_data["category"],
                severity=rule_data["severity"],
                rule_text=rule_data["rule_text"],
                keywords=rule_data.get("keywords", []),
                points_deduction=rule_data.get("points_deduction", -5.0),
                is_auto_generated=True,
                generated_from_industry=industry,
                generation_source=rule_data.get("source_url", "onboarding"),
                confidence_score=rule_data.get("confidence_score", 0.8),
                is_active=True
            )
            db.add(rule)
        
        db.commit()
        
        logger.info(
            f"Onboarding complete: {len(all_rules)} rules generated "
            f"across {len(rules_by_category)} categories"
        )
        
        return {
            "rules_generated": len(all_rules),
            "by_category": rules_by_category,
            "sources_used": list(set(sources_used)) if sources_used else ["rag_fallback"]
        }
    
    async def complete_onboarding(
        self,
        user_id: UUID,
        industry: str,
        brand_name: str,
        brand_guidelines: str,
        analysis_scope: List[str],
        db: Session
    ) -> Dict[str, Any]:
        """
        Complete user onboarding workflow.
        
        1. Save user config
        2. Generate rules
        3. Mark onboarding as complete
        
        Returns summary of onboarding results.
        """
        # Check if config already exists
        existing_config = db.query(UserConfig).filter_by(user_id=user_id).first()
        
        if existing_config:
            # Update existing
            existing_config.industry = industry
            existing_config.brand_name = brand_name
            existing_config.brand_guidelines = brand_guidelines
            existing_config.analysis_scope = analysis_scope
            existing_config.onboarding_completed = True
            db.commit()
            logger.info(f"Updated existing config for user {user_id}")
        else:
            # Create new config
            config = UserConfig(
                user_id=user_id,
                industry=industry,
                brand_name=brand_name,
                brand_guidelines=brand_guidelines,
                analysis_scope=analysis_scope,
                onboarding_completed=True
            )
            db.add(config)
            db.commit()
            logger.info(f"Created new config for user {user_id}")
        
        # Generate rules
        rule_summary = await self.generate_rules_from_onboarding(
            user_id=user_id,
            industry=industry,
            brand_name=brand_name,
            analysis_scope=analysis_scope,
            db=db
        )
        
        return {
            "success": True,
            "config_created": True,
            **rule_summary
        }


# Singleton instance
onboarding_service = OnboardingService()
