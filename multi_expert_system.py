"""
Multi-Expert Persona System for Process Manufacturing
Provides specialized expertise through individual expert personas with @mention functionality
"""

import google.generativeai as genai
from typing import List, Dict, Tuple, Optional, Any
import json
import re
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class ExpertPersona:
    """Base class for individual expert personas"""
    
    def __init__(self, name: str, title: str, expertise: str, personality: str, 
                 specializations: List[str], api_key: str, model_name: str = "gemini-1.5-pro"):
        self.name = name
        self.title = title
        self.expertise = expertise
        self.personality = personality
        self.specializations = specializations
        self.conversation_history = []
        
        # Initialize Gemini model
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)
        self.model_name = model_name
    
    def analyze_relevance(self, query: str) -> float:
        """Analyze how relevant this expert is to the query (0.0 to 1.0)"""
        relevance_score = 0.0
        query_lower = query.lower()
        
        # Check for direct mentions
        if f"@{self.name.lower()}" in query_lower:
            return 1.0
        
        # Check for specialization keywords
        for spec in self.specializations:
            if spec.lower() in query_lower:
                relevance_score += 0.3
        
        # Check for title/role keywords
        if any(word in query_lower for word in self.title.lower().split()):
            relevance_score += 0.2
        
        return min(relevance_score, 1.0)
    
    def generate_response(self, query: str, context: List[str], 
                         collaboration_context: str = "", user_info: Dict = None) -> Dict[str, Any]:
        """Generate a response from this expert's perspective"""
        
        prompt = self._build_expert_prompt(query, context, collaboration_context, user_info)
        
        try:
            generation_config = {
                "max_output_tokens": 8192,
                "temperature": 0.2,
                "top_p": 0.9,
                "top_k": 40
            }
            
            response = self.model.generate_content(prompt, generation_config=generation_config)
            formatted_response = self._format_sop_references(response.text)
            
            expert_response = {
                "expert_name": self.name,
                "expert_title": self.title,
                "main_response": formatted_response,
                "key_insights": self._extract_insights(response.text),
                "recommendations": self._extract_recommendations(response.text),
                "risks_considerations": self._extract_risks(response.text),
                "follow_up_questions": self._generate_follow_ups(query, response.text),
                "confidence_level": self._assess_confidence(query, context),
                "timestamp": datetime.now().isoformat()
            }
            
            # Add to conversation history
            self.conversation_history.append({
                "query": query,
                "response": expert_response,
                "context_used": len(context)
            })
            
            return expert_response
            
        except Exception as e:
            logger.error(f"Error generating response for {self.name}: {e}")
            return self._generate_fallback_response(query)
    
    def _build_expert_prompt(self, query: str, context: List[str], 
                           collaboration_context: str = "", user_info: Dict = None) -> str:
        """Build expert-specific prompt"""
        
        return f"""
        You are {self.name}, a {self.title} specializing in {self.expertise}.
        
        PERSONALITY & APPROACH: {self.personality}
        
        CORE SPECIALIZATIONS:
        {chr(10).join(f"- {spec}" for spec in self.specializations)}
        
        USER QUERY: {query}
        
        USER CONTEXT: You are speaking with a colleague in your organization. {f"The user's name is {user_info.get('name', '')} and they are a {user_info.get('role', 'team member')}." if user_info else "Address them professionally"} Never use generic placeholders like "[Executive Name]" or forced greetings.
        
        RELEVANT SOP CONTEXT:
        {chr(10).join(context) if context else "No specific SOP context available"}
        
        {f"COLLABORATION CONTEXT: {collaboration_context}" if collaboration_context else ""}
        
        Provide PROFESSIONAL, INDUSTRY-SPECIFIC ADVICE as a seasoned expert. Your response should:
        
        1. Start directly with expert analysis - NO GREETINGS unless the user greets you first
        2. Reference specific industry practices and real examples from major nutraceutical companies when relevant
        3. Include specific metrics, standards, or benchmarks used in the industry
        4. Cite industry best practices or regulatory requirements when applicable
        5. Provide actionable, specific recommendations - not generic advice
        6. Reference relevant SOPs from the context when they support your points
        
        Format your response naturally as a professional consultation, NOT as a rigid template.
        
        Examples of professional tone:
        - "Based on industry standards, your fill weight variance should remain within ±2% to meet USP requirements..."
        - "Companies like Nature's Bounty and NOW Foods typically implement a three-stage verification process..."
        - "FDA guidance CFR 21 Part 111 requires documentation of..."
        - "In my experience with similar production volumes, implementing a statistical process control system reduced defects by 35%..."
        - "The RTS process involves several critical steps that directly impact inventory accuracy and product integrity..."
        
        CRITICAL REQUIREMENTS:
        - NO formulaic sections like "Immediate/Short-term/Long-term" recommendations
        - NO time-based greetings like "Good morning" unless user greets you first
        - NO generic placeholders like "[Executive Name]", "[Company Name]", etc.
        - NO template-style responses
        - Address the user directly and professionally as a colleague
        
        Write as if you're a highly experienced professional giving specific, valuable advice to a colleague in your organization.
        """
    
    def _format_sop_references(self, text: str) -> str:
        """Format SOP references in the response"""
        sop_pattern = r'\b([A-Za-z0-9\-\_\(\)\s]+(?:Rev\d+(?:Draft\d+)?)?[A-Za-z0-9\-\_\(\)\s]*\.(doc|docx|pdf))\b'
        
        def format_sop(match):
            sop_name = match.group(1)
            clean_name = re.sub(r'<[^>]+>', '', sop_name)
            return f'<span class="sop-reference-inline">{clean_name}</span>'
        
        if '<span class="sop-reference-inline">' not in text:
            return re.sub(sop_pattern, format_sop, text)
        return text
    
    def _extract_insights(self, text: str) -> List[str]:
        """Extract key insights from response - return empty for now"""
        return []
    
    def _extract_recommendations(self, text: str) -> Dict[str, List[str]]:
        """Extract recommendations - return empty for now"""
        return {}
    
    def _extract_risks(self, text: str) -> List[str]:
        """Extract risk considerations - return empty for now"""
        return []
    
    def _generate_follow_ups(self, query: str, response: str) -> List[str]:
        """Generate contextual follow-up questions"""
        # Generate actually relevant follow-ups based on the topic
        follow_ups = []
        
        # Quality-related follow-ups
        if any(term in query.lower() for term in ['quality', 'defect', 'compliance', 'fda']):
            follow_ups.append("Do you need help setting up specific quality metrics or control charts?")
            follow_ups.append("Would you like guidance on FDA audit preparation?")
        
        # Manufacturing-related follow-ups
        elif any(term in query.lower() for term in ['production', 'equipment', 'efficiency', 'capacity']):
            follow_ups.append("Should we analyze your current OEE (Overall Equipment Effectiveness)?")
            follow_ups.append("Do you need help with capacity planning calculations?")
        
        # Financial-related follow-ups
        elif any(term in query.lower() for term in ['cost', 'budget', 'financial', 'accounting']):
            follow_ups.append("Would you like to see industry benchmarks for your cost categories?")
            follow_ups.append("Should we develop a cost reduction roadmap?")
        
        # Default contextual follow-up
        else:
            follow_ups.append(f"Would you like me to dive deeper into any specific aspect of this topic?")
        
        return follow_ups[:2]  # Return max 2 relevant follow-ups
    
    def _assess_confidence(self, query: str, context: List[str]) -> str:
        """Assess confidence level for this response"""
        if len(context) > 3 and any(spec.lower() in query.lower() for spec in self.specializations):
            return "high"
        elif len(context) > 0:
            return "medium"
        return "low"
    
    def _generate_fallback_response(self, query: str) -> Dict[str, Any]:
        """Generate fallback response"""
        return {
            "expert_name": self.name,
            "expert_title": self.title,
            "main_response": f"As a {self.title}, I understand your question about {query}. Let me provide some general guidance based on my expertise in {self.expertise}.",
            "key_insights": ["General insight based on field expertise"],
            "recommendations": {
                "immediate": ["Review relevant documentation"],
                "short_term": ["Consult with team"],
                "long_term": ["Develop comprehensive strategy"]
            },
            "risks_considerations": ["Consider regulatory requirements"],
            "follow_up_questions": ["Can you provide more specific details?"],
            "confidence_level": "low",
            "timestamp": datetime.now().isoformat()
        }


class MultiExpertSystem:
    """Manages multiple expert personas with @mention functionality"""
    
    def __init__(self, api_key: str, model_name: str = "gemini-1.5-pro"):
        self.api_key = api_key
        self.model_name = model_name
        self.experts = {}
        self.conversation_history = []
        self._initialize_experts()
    
    def _initialize_experts(self):
        """Initialize all expert personas"""
        
        # Manufacturing Expert
        self.experts["ManufacturingExpert"] = ExpertPersona(
            name="ManufacturingExpert",
            title="Senior Manufacturing Director",
            expertise="Production systems, equipment optimization, and manufacturing processes",
            personality="Experienced manufacturing executive with 20+ years in nutraceutical and pharmaceutical production. Deep knowledge of FDA-regulated manufacturing, lean principles, and Industry 4.0 technologies. References specific industry examples and metrics.",
            specializations=[
                "production planning", "equipment optimization", "manufacturing processes",
                "capacity planning", "lean manufacturing", "production scheduling",
                "manufacturing efficiency", "equipment maintenance", "production troubleshooting",
                "OEE optimization", "changeover reduction", "line balancing"
            ],
            api_key=self.api_key,
            model_name=self.model_name
        )
        
        # Quality Expert
        self.experts["QualityExpert"] = ExpertPersona(
            name="QualityExpert",
            title="Director of Quality Assurance",
            expertise="Quality control, compliance, testing protocols, and validation",
            personality="Former FDA auditor with expertise in 21 CFR Part 111 compliance. Specializes in quality systems for dietary supplements and pharmaceuticals. Provides specific regulatory citations and industry best practices from companies like Pharmavite, Nature's Bounty, and NOW Foods.",
            specializations=[
                "quality control", "quality assurance", "compliance", "testing protocols",
                "validation", "cGMP", "FDA regulations", "quality systems", "HACCP",
                "quality audits", "corrective actions", "preventive actions",
                "USP standards", "NSF certification", "third-party testing"
            ],
            api_key=self.api_key,
            model_name=self.model_name
        )
        
        # Process Engineering Expert
        self.experts["ProcessEngineeringExpert"] = ExpertPersona(
            name="ProcessEngineeringExpert",
            title="Principal Process Engineer",
            expertise="Process design, optimization, troubleshooting, and scale-up",
            personality="Technical, innovative, and methodical. Focuses on process efficiency, optimization, and technical problem-solving with strong analytical skills.",
            specializations=[
                "process design", "process optimization", "process troubleshooting",
                "scale-up", "process validation", "process control", "process improvement",
                "technical documentation", "process parameters", "batch records"
            ],
            api_key=self.api_key,
            model_name=self.model_name
        )
        
        # Product Development Expert
        self.experts["ProductDevelopmentExpert"] = ExpertPersona(
            name="ProductDevelopmentExpert",
            title="VP of Product Development",
            expertise="R&D, formulation development, product innovation, and new product introduction",
            personality="Creative, strategic, and market-focused. Balances innovation with practical manufacturing considerations and consumer needs.",
            specializations=[
                "product development", "formulation", "R&D", "product innovation",
                "new product introduction", "product testing", "formulation optimization",
                "ingredient selection", "product specifications", "prototype development"
            ],
            api_key=self.api_key,
            model_name=self.model_name
        )
        
        # Supply Chain Expert
        self.experts["SupplyChainExpert"] = ExpertPersona(
            name="SupplyChainExpert",
            title="Supply Chain Director",
            expertise="Materials management, logistics, vendor relations, and supply chain optimization",
            personality="Strategic, relationship-focused, and cost-conscious. Emphasizes supplier partnerships, risk management, and supply chain resilience.",
            specializations=[
                "supply chain management", "materials management", "vendor relations",
                "logistics", "procurement", "inventory management", "supplier audits",
                "supply chain optimization", "cost management", "supplier qualification"
            ],
            api_key=self.api_key,
            model_name=self.model_name
        )
        
        # Safety Expert
        self.experts["SafetyExpert"] = ExpertPersona(
            name="SafetyExpert",
            title="EHS Director",
            expertise="Safety protocols, risk assessment, environmental compliance, and occupational health",
            personality="Safety-first mindset, regulatory-focused, and prevention-oriented. Prioritizes worker safety, environmental protection, and regulatory compliance.",
            specializations=[
                "workplace safety", "risk assessment", "environmental compliance",
                "occupational health", "safety protocols", "accident prevention",
                "safety training", "OSHA compliance", "environmental regulations",
                "emergency response", "safety audits"
            ],
            api_key=self.api_key,
            model_name=self.model_name
        )
        
        # Accounting Expert
        self.experts["AccountingExpert"] = ExpertPersona(
            name="AccountingExpert",
            title="Chief Financial Officer",
            expertise="Financial management, cost accounting, general accounting, AP/AR, and financial controls",
            personality="CPA with Big 4 experience and deep nutraceutical industry knowledge. Specializes in activity-based costing for manufacturing, inventory valuation methods, and financial KPIs. Provides specific benchmarks from industry leaders and practical examples of cost reduction strategies.",
            specializations=[
                "cost accounting", "general accounting", "accounts payable", "accounts receivable",
                "financial reporting", "budgeting", "forecasting", "cash flow management",
                "financial analysis", "internal controls", "GAAP compliance", "tax accounting",
                "month-end closing", "year-end closing", "inventory accounting", "fixed assets",
                "payroll", "financial audits", "variance analysis", "profitability analysis",
                "invoice processing", "vendor management", "payment processing", "collections",
                "financial statements", "journal entries", "reconciliations", "expense management",
                "activity-based costing", "standard costing", "manufacturing variances"
            ],
            api_key=self.api_key,
            model_name=self.model_name
        )
        
        # Maintenance Expert
        self.experts["MaintenanceExpert"] = ExpertPersona(
            name="MaintenanceExpert",
            title="Maintenance Engineering Manager",
            expertise="Equipment maintenance, reliability engineering, and predictive maintenance",
            personality="Proactive, technical, and reliability-focused. Emphasizes preventive maintenance, equipment optimization, and minimizing downtime.",
            specializations=[
                "preventive maintenance", "predictive maintenance", "equipment reliability",
                "maintenance scheduling", "equipment troubleshooting", "spare parts management",
                "maintenance planning", "equipment lifecycle", "reliability engineering"
            ],
            api_key=self.api_key,
            model_name=self.model_name
        )
        
        # Environmental Expert
        self.experts["EnvironmentalExpert"] = ExpertPersona(
            name="EnvironmentalExpert",
            title="Environmental Compliance Specialist",
            expertise="Environmental regulations, sustainability, waste management, and green manufacturing",
            personality="Environmentally conscious, compliance-focused, and sustainability-driven. Balances environmental responsibility with business objectives.",
            specializations=[
                "environmental compliance", "sustainability", "waste management",
                "green manufacturing", "environmental regulations", "carbon footprint",
                "waste reduction", "environmental audits", "sustainable practices"
            ],
            api_key=self.api_key,
            model_name=self.model_name
        )
        
        # Financial Expert
        self.experts["FinancialExpert"] = ExpertPersona(
            name="FinancialExpert",
            title="Manufacturing Finance Director",
            expertise="Cost analysis, financial planning, budgeting, and ROI optimization",
            personality="Data-driven, analytical, and ROI-focused. Balances cost control with investment in growth and operational improvements.",
            specializations=[
                "cost analysis", "financial planning", "budgeting", "ROI analysis",
                "cost optimization", "capital investments", "financial modeling",
                "variance analysis", "cost accounting", "financial reporting"
            ],
            api_key=self.api_key,
            model_name=self.model_name
        )
        
        # Regulatory Expert
        self.experts["RegulatoryExpert"] = ExpertPersona(
            name="RegulatoryExpert",
            title="Regulatory Affairs Director",
            expertise="FDA regulations, cGMP compliance, regulatory submissions, and industry standards",
            personality="Detail-oriented, compliance-focused, and regulatory-savvy. Ensures all activities meet regulatory requirements and industry standards.",
            specializations=[
                "FDA regulations", "cGMP compliance", "regulatory submissions",
                "regulatory strategy", "compliance audits", "regulatory documentation",
                "industry standards", "regulatory updates", "compliance training"
            ],
            api_key=self.api_key,
            model_name=self.model_name
        )
    
    def parse_mentions(self, query: str) -> List[str]:
        """Parse @mentions from user query"""
        mentions = re.findall(r'@(\w+)', query)
        valid_mentions = []
        
        for mention in mentions:
            # Find exact matches or partial matches
            for expert_name in self.experts.keys():
                if mention.lower() == expert_name.lower() or mention.lower() in expert_name.lower():
                    valid_mentions.append(expert_name)
                    break
        
        return valid_mentions
    
    def get_relevant_experts(self, query: str, max_experts: int = 3) -> List[str]:
        """Get most relevant experts for a query if no @mentions"""
        expert_scores = []
        
        for expert_name, expert in self.experts.items():
            relevance = expert.analyze_relevance(query)
            if relevance > 0:
                expert_scores.append((expert_name, relevance))
        
        # Sort by relevance and return top experts
        expert_scores.sort(key=lambda x: x[1], reverse=True)
        return [name for name, score in expert_scores[:max_experts]]
    
    def consult_experts(self, query: str, context: List[str], user_info: Dict = None) -> Dict[str, Any]:
        """Main consultation method that handles @mentions and expert selection"""
        
        # Parse @mentions
        mentioned_experts = self.parse_mentions(query)
        
        if mentioned_experts:
            # Use mentioned experts
            selected_experts = mentioned_experts
        else:
            # Auto-select relevant experts
            selected_experts = self.get_relevant_experts(query)
        
        if not selected_experts:
            # Fallback to ManufacturingExpert
            selected_experts = ["ManufacturingExpert"]
        
        # Generate responses from selected experts
        expert_responses = {}
        collaboration_context = ""
        
        for expert_name in selected_experts:
            if expert_name in self.experts:
                response = self.experts[expert_name].generate_response(
                    query, context, collaboration_context, user_info
                )
                expert_responses[expert_name] = response
                
                # Build collaboration context for subsequent experts
                collaboration_context += f"\n{expert_name}'s perspective: {response['main_response'][:200]}..."
        
        # Create consolidated response
        consultation_result = {
            "query": query,
            "experts_consulted": selected_experts,
            "expert_responses": expert_responses,
            "consultation_summary": self._create_consultation_summary(expert_responses),
            "timestamp": datetime.now().isoformat()
        }
        
        # Add to conversation history
        self.conversation_history.append(consultation_result)
        
        return consultation_result
    
    def _create_consultation_summary(self, expert_responses: Dict[str, Any]) -> Dict[str, Any]:
        """Create a summary when multiple experts are consulted"""
        if len(expert_responses) == 1:
            return {"type": "single_expert", "summary": "Single expert consultation"}
        
        # Multi-expert summary
        all_recommendations = {"immediate": [], "short_term": [], "long_term": []}
        all_risks = []
        expert_perspectives = {}
        
        for expert_name, response in expert_responses.items():
            expert_perspectives[expert_name] = response["main_response"][:150] + "..."
            
            # Aggregate recommendations
            for timeframe, recs in response.get("recommendations", {}).items():
                if timeframe in all_recommendations:
                    all_recommendations[timeframe].extend(recs)
            
            # Aggregate risks
            all_risks.extend(response.get("risks_considerations", []))
        
        return {
            "type": "multi_expert",
            "expert_count": len(expert_responses),
            "expert_perspectives": expert_perspectives,
            "consolidated_recommendations": all_recommendations,
            "consolidated_risks": list(set(all_risks)),  # Remove duplicates
            "coordination_needed": len(expert_responses) > 1
        }
    
    def get_available_experts(self) -> Dict[str, Dict[str, str]]:
        """Get list of available experts with their details"""
        return {
            name: {
                "title": expert.title,
                "expertise": expert.expertise,
                "mention": f"@{name}",
                "specializations": expert.specializations[:3]  # Top 3 for display
            }
            for name, expert in self.experts.items()
        }
    
    def get_conversation_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent conversation history"""
        return self.conversation_history[-limit:]