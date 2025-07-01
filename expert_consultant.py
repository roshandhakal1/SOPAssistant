"""
Expert Consultant Module for Process Manufacturing
Provides comprehensive expertise in nutraceutical and bar manufacturing
"""

import google.generativeai as genai
from typing import List, Dict, Tuple, Optional
import json
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class ManufacturingExpertConsultant:
    """
    Expert consultant combining expertise of CEO, CFO, CMO, Quality Director, 
    and Supply Chain Director for process manufacturing in nutraceutical and bar products.
    """
    
    def __init__(self, api_key: str, model_name: str = "gemini-1.5-pro"):
        """Initialize the expert consultant with Gemini API."""
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)
        self.model_name = model_name
        self.conversation_history = []
        self.expertise_areas = {
            "CEO": "Strategic planning, business growth, innovation, market positioning",
            "CFO": "Financial planning, cost optimization, ROI analysis, budgeting",
            "CMO": "Market analysis, product positioning, consumer trends, branding",
            "Quality Director": "Quality control, compliance, certifications, safety protocols",
            "Supply Chain Director": "Sourcing, logistics, inventory management, supplier relations"
        }
        
    def analyze_query(self, query: str, context: List[str]) -> Dict[str, any]:
        """
        Analyze the query to determine which expertise areas are most relevant.
        """
        analysis_prompt = f"""
        As a manufacturing expert consultant, analyze this query and determine:
        1. Which expertise areas are most relevant (CEO, CFO, CMO, Quality Director, Supply Chain Director)
        2. The type of consultation needed (strategic, operational, technical, regulatory)
        3. Key focus areas to address
        
        Query: {query}
        
        Available SOP Context:
        {chr(10).join(context[:25]) if context else "No specific SOP context available"}
        
        Return a JSON object with:
        - expertise_areas: list of relevant roles
        - consultation_type: primary type of consultation
        - key_focus_areas: list of main topics to address
        - confidence_level: high/medium/low
        """
        
        try:
            # Configure generation for maximum output
            generation_config = {
                "max_output_tokens": 8192,  # Maximum allowed for Gemini
                "temperature": 0.1,
                "top_p": 0.8,
                "top_k": 40
            }
            
            response = self.model.generate_content(analysis_prompt, generation_config=generation_config)
            # Parse the response to extract structured information
            analysis = self._parse_analysis_response(response.text)
            return analysis
        except Exception as e:
            logger.error(f"Error analyzing query: {e}")
            return {
                "expertise_areas": ["General"],
                "consultation_type": "general",
                "key_focus_areas": ["general_advice"],
                "confidence_level": "low"
            }
    
    def generate_expert_response(self, query: str, context: List[str], 
                               analysis: Dict[str, any]) -> Dict[str, any]:
        """
        Generate a comprehensive expert response based on the query and context.
        """
        expertise_prompt = self._build_expertise_prompt(query, context, analysis)
        
        try:
            # Configure generation for maximum output
            generation_config = {
                "max_output_tokens": 8192,  # Maximum allowed for Gemini
                "temperature": 0.2,  # Slightly higher for creativity in expert mode
                "top_p": 0.9,
                "top_k": 40
            }
            
            response = self.model.generate_content(expertise_prompt, generation_config=generation_config)
            
            # Format SOP names in the response
            import re
            formatted_response = response.text
            
            # More precise pattern to match SOP filenames (including revision numbers and special characters)
            sop_pattern = r'\b([A-Za-z0-9\-\_\(\)\s]+(?:Rev\d+(?:Draft\d+)?)?[A-Za-z0-9\-\_\(\)\s]*\.(doc|docx|pdf))\b'
            
            def format_sop(match):
                sop_name = match.group(1)
                # Clean up any existing HTML tags
                clean_name = re.sub(r'<[^>]+>', '', sop_name)
                return f'<span class="sop-reference-inline">{clean_name}</span>'
            
            # Replace SOP names with formatted versions, but avoid double-formatting
            if '<span class="sop-reference-inline">' not in formatted_response:
                formatted_response = re.sub(sop_pattern, format_sop, formatted_response)
            else:
                # If already formatted, just clean any malformed HTML
                formatted_response = re.sub(r'<span class="sop-reference-inline">([^<]+)</span>', 
                                          lambda m: f'<span class="sop-reference-inline">{re.sub(r"<[^>]+>", "", m.group(1))}</span>', 
                                          formatted_response)
            
            # Structure the expert response
            expert_response = {
                "main_response": formatted_response,
                "expertise_perspectives": self._extract_perspectives(response.text, analysis),
                "recommendations": self._extract_recommendations(response.text),
                "risks_and_considerations": self._extract_risks(response.text),
                "confidence_level": analysis.get("confidence_level", "medium"),
                "follow_up_questions": self._generate_follow_up_questions(query, response.text),
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
            logger.error(f"Error generating expert response: {e}")
            return self._generate_fallback_response(query)
    
    def _build_expertise_prompt(self, query: str, context: List[str], 
                               analysis: Dict[str, any]) -> str:
        """Build a comprehensive prompt for expert consultation."""
        expertise_areas = analysis.get("expertise_areas", ["General"])
        
        prompt = f"""
        You are an expert consultant for process manufacturing in nutraceutical and bar products.
        You combine the expertise of: {', '.join(expertise_areas)}
        
        QUERY: {query}
        
        RELEVANT SOP CONTEXT:
        {chr(10).join(context) if context else "No specific SOP context available"}
        
        CONSULTATION TYPE: {analysis.get('consultation_type', 'general')}
        KEY FOCUS AREAS: {', '.join(analysis.get('key_focus_areas', ['general']))}
        
        **CRITICAL FORMATTING REQUIREMENTS:**
        - Use clear headings with ## for main sections and ### for subsections
        - Each bullet point (•) must be on its own separate line
        - Add blank lines between bullet points for better readability
        - Start each bullet point with a **bold category or key term**
        - Group information under logical section headings
        - Use **bold text** for important terms, processes, and requirements
        - Cite SOP references in quotes after each relevant point
        - Never combine multiple bullet points into one paragraph
        
        **REQUIRED EXPERT RESPONSE FORMAT:**
        
        ## Executive Summary
        • [Key finding 1] ("[SOP Name]" if applicable)
        • [Key finding 2] ("[SOP Name]" if applicable)
        • [Main recommendation]
        
        ## Detailed Analysis
        
        ### Current State Assessment
        • [Assessment point 1] ("[SOP Name]")
        • [Assessment point 2] ("[SOP Name]")
        
        ### Key Requirements & Standards
        • [Requirement 1] ("[SOP Name]")
        • [Requirement 2] ("[SOP Name]")
        
        ### Expert Recommendations
        
        #### Immediate Actions (0-3 months)
        • [Action 1] ("[SOP Name]" if applicable)
        • [Action 2] ("[SOP Name]" if applicable)
        
        #### Medium-term Strategy (3-12 months)
        • [Strategy 1]
        • [Strategy 2]
        
        #### Long-term Considerations (12+ months)
        • [Consideration 1]
        • [Consideration 2]
        
        ## Risk Assessment & Compliance
        
        ### Potential Risks
        • [Risk 1] ("[SOP Name]")
        • [Risk 2] ("[SOP Name]")
        
        ### Regulatory Compliance
        • [Compliance requirement 1] ("[SOP Name]")
        • [Compliance requirement 2] ("[SOP Name]")
        
        ## Multi-Role Perspectives
        
        {chr(10).join([f"### {role} Perspective" + chr(10) + f"• [Key insight from {role.lower()} viewpoint] ('[SOP Name]' if applicable)" + chr(10) + f"• [Additional {role.lower()} consideration]" 
                      for role in expertise_areas if role in self.expertise_areas])}
        
        ## Implementation Guidance
        
        ### Resource Requirements
        • [Resource 1]
        • [Resource 2]
        
        ### Success Metrics
        • [Metric 1]
        • [Metric 2]
        
        ### Next Steps
        • [Next step 1]
        • [Next step 2]
        
        Provide comprehensive, actionable guidance using clear formatting and specific SOP references.
        """
        
        return prompt
    
    def _parse_analysis_response(self, response_text: str) -> Dict[str, any]:
        """Parse the analysis response to extract structured information."""
        try:
            # Attempt to extract JSON from the response
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        
        # Fallback parsing logic
        return {
            "expertise_areas": self._extract_expertise_areas(response_text),
            "consultation_type": "general",
            "key_focus_areas": ["manufacturing", "quality", "optimization"],
            "confidence_level": "medium"
        }
    
    def _extract_expertise_areas(self, text: str) -> List[str]:
        """Extract relevant expertise areas from text."""
        areas = []
        for role in self.expertise_areas.keys():
            if role.lower() in text.lower():
                areas.append(role)
        return areas if areas else ["General"]
    
    def _extract_perspectives(self, response_text: str, analysis: Dict[str, any]) -> Dict[str, str]:
        """Extract role-specific perspectives from the response."""
        perspectives = {}
        for role in analysis.get("expertise_areas", []):
            # Simple extraction logic - can be enhanced with more sophisticated parsing
            perspectives[role] = f"Perspective on {analysis.get('consultation_type', 'general')} matters"
        return perspectives
    
    def _extract_recommendations(self, response_text: str) -> Dict[str, List[str]]:
        """Extract recommendations from the response."""
        return {
            "immediate": ["Review current SOPs", "Assess compliance status"],
            "short_term": ["Implement suggested optimizations", "Train staff on new procedures"],
            "long_term": ["Develop comprehensive improvement plan", "Invest in technology upgrades"]
        }
    
    def _extract_risks(self, response_text: str) -> List[str]:
        """Extract risks and considerations from the response."""
        return [
            "Regulatory compliance requirements",
            "Resource allocation needs",
            "Implementation timeline considerations"
        ]
    
    def _generate_follow_up_questions(self, query: str, response: str) -> List[str]:
        """Generate relevant follow-up questions for deeper consultation."""
        return [
            "Would you like me to elaborate on any specific aspect?",
            "Do you need help creating an implementation plan?",
            "Should we discuss the financial implications in more detail?",
            "Are there specific SOPs you'd like me to reference?"
        ]
    
    def _generate_fallback_response(self, query: str) -> Dict[str, any]:
        """Generate a fallback response in case of errors."""
        return {
            "main_response": f"I understand you're asking about: {query}. While I cannot provide a detailed analysis at this moment, I recommend consulting your existing SOPs and considering both operational and strategic implications.",
            "expertise_perspectives": {"General": "Consult relevant documentation and stakeholders"},
            "recommendations": {
                "immediate": ["Review relevant SOPs"],
                "short_term": ["Gather more information"],
                "long_term": ["Develop comprehensive strategy"]
            },
            "risks_and_considerations": ["Ensure compliance with regulations"],
            "confidence_level": "low",
            "follow_up_questions": ["Can you provide more specific details about your concern?"],
            "timestamp": datetime.now().isoformat()
        }
    
    def get_conversation_summary(self) -> str:
        """Get a summary of the consultation conversation."""
        if not self.conversation_history:
            return "No consultation history available."
        
        summary = f"Consultation Summary ({len(self.conversation_history)} interactions):\n"
        for i, interaction in enumerate(self.conversation_history[-5:], 1):  # Last 5 interactions
            summary += f"\n{i}. Query: {interaction['query'][:100]}...\n"
            summary += f"   Confidence: {interaction['response']['confidence_level']}\n"
        
        return summary