"""Unified workflow service integrating LangGraph workflows with meeting processing."""

from __future__ import annotations

import logging
from typing import Any
from langgraph.graph import StateGraph, END

from agent_service.xg_agent.agent import Agent, AgentState, create_agent_workflow
from agent_service.config import get_settings

logger = logging.getLogger(__name__)


class UnifiedWorkflowService:
	"""
	Service to integrate LangGraph workflows with meeting processing.
	"""
	
	def __init__(self):
		self.settings = get_settings()
		self.agent = Agent()
	
	def create_meeting_analysis_workflow(self):
		"""
		Creates a unified workflow that combines:
		1. Meeting transcription (ASR)
		2. XG Agent analysis (sentiment, action items, insights)
		3. Combined summary generation
		"""
		workflow = StateGraph(AgentState)
		
		# Add nodes for meeting analysis
		workflow.add_node("analyze_transcript", self._analyze_transcript_node)
		workflow.add_node("extract_action_items", self._extract_action_items_node)
		workflow.add_node("sentiment_analysis", self._sentiment_analysis_node)
		workflow.add_node("generate_insights", self._generate_insights_node)
		workflow.add_node("combine_summary", self._combine_summary_node)
		
		# Set workflow edges
		workflow.set_entry_point("analyze_transcript")
		workflow.add_edge("analyze_transcript", "extract_action_items")
		workflow.add_edge("extract_action_items", "sentiment_analysis")
		workflow.add_edge("sentiment_analysis", "generate_insights")
		workflow.add_edge("generate_insights", "combine_summary")
		workflow.add_edge("combine_summary", END)
		
		return workflow
	
	def _analyze_transcript_node(self, state: AgentState) -> AgentState:
		"""
		Analyze meeting transcript for key information.
		Expects transcript text in state["data"]["transcript"]
		"""
		logger.info("---ANALYZING TRANSCRIPT---")
		
		transcript = state.get("data", {}).get("transcript", "")
		if not transcript:
			raise ValueError("No transcript found in state data")
		
		# Store transcript for later nodes
		state["data"]["transcript_analyzed"] = True
		return state
	
	def _extract_action_items_node(self, state: AgentState) -> AgentState:
		"""
		Extract action items from meeting transcript.
		"""
		logger.info("---EXTRACTING ACTION ITEMS---")
		
		transcript = state.get("data", {}).get("transcript", "")
		
		from langchain_core.prompts import ChatPromptTemplate
		from langchain_core.output_parsers import StrOutputParser
		
		prompt = ChatPromptTemplate.from_template(
			"""
			Extract all actionable items from the following meeting transcript.
			For each action item, provide:
			- Who is responsible (if mentioned)
			- What needs to be done
			- Deadline (if mentioned)
			- Priority level (high/medium/low)
			
			Transcript:
			{transcript}
			
			Return a JSON array of action items.
			"""
		)
		
		chain = prompt | self.agent.llm | StrOutputParser()
		action_items_text = chain.invoke({"transcript": transcript})
		
		# Parse JSON response
		import json
		try:
			action_items = json.loads(action_items_text)
		except json.JSONDecodeError:
			action_items = [{"raw": action_items_text}]
		
		state["analysis_results"]["action_items"] = action_items
		return state
	
	def _sentiment_analysis_node(self, state: AgentState) -> AgentState:
		"""
		Perform sentiment analysis on meeting transcript.
		"""
		logger.info("---PERFORMING SENTIMENT ANALYSIS---")
		
		transcript = state.get("data", {}).get("transcript", "")
		
		from langchain_core.prompts import ChatPromptTemplate
		from langchain_core.output_parsers import StrOutputParser
		
		prompt = ChatPromptTemplate.from_template(
			"""
			Analyze the sentiment of the following meeting transcript.
			Provide:
			- Overall sentiment (positive/neutral/negative)
			- Sentiment score (0-1, where 1 is most positive)
			- Key positive points
			- Key concerns or negative points
			- Emotional tone
			
			Transcript:
			{transcript}
			
			Return a JSON object with these fields.
			"""
		)
		
		chain = prompt | self.agent.llm | StrOutputParser()
		sentiment_text = chain.invoke({"transcript": transcript})
		
		# Parse JSON response
		import json
		try:
			sentiment_result = json.loads(sentiment_text)
		except json.JSONDecodeError:
			sentiment_result = {"raw": sentiment_text}
		
		state["analysis_results"]["sentiment"] = sentiment_result
		return state
	
	def _generate_insights_node(self, state: AgentState) -> AgentState:
		"""
		Generate business insights from meeting transcript.
		"""
		logger.info("---GENERATING INSIGHTS---")
		
		transcript = state.get("data", {}).get("transcript", "")
		action_items = state.get("analysis_results", {}).get("action_items", [])
		sentiment = state.get("analysis_results", {}).get("sentiment", {})
		
		from langchain_core.prompts import ChatPromptTemplate
		from langchain_core.output_parsers import StrOutputParser
		
		prompt = ChatPromptTemplate.from_template(
			"""
			Based on the meeting transcript, extracted action items, and sentiment analysis,
			provide key business insights:
			
			1. Main themes and topics discussed
			2. Key decisions made
			3. Opportunities identified
			4. Risks or concerns raised
			5. Recommendations for follow-up
			
			Transcript:
			{transcript}
			
			Action Items:
			{action_items}
			
			Sentiment:
			{sentiment}
			
			Return a JSON object with these insights.
			"""
		)
		
		chain = prompt | self.agent.llm | StrOutputParser()
		insights_text = chain.invoke({
			"transcript": transcript,
			"action_items": action_items,
			"sentiment": sentiment
		})
		
		# Parse JSON response
		import json
		try:
			insights = json.loads(insights_text)
		except json.JSONDecodeError:
			insights = {"raw": insights_text}
		
		state["analysis_results"]["insights"] = insights
		return state
	
	def _combine_summary_node(self, state: AgentState) -> AgentState:
		"""
		Generate a comprehensive summary combining all analysis results.
		"""
		logger.info("---GENERATING COMBINED SUMMARY---")
		
		transcript = state.get("data", {}).get("transcript", "")
		action_items = state.get("analysis_results", {}).get("action_items", [])
		sentiment = state.get("analysis_results", {}).get("sentiment", {})
		insights = state.get("analysis_results", {}).get("insights", {})
		
		from langchain_core.prompts import ChatPromptTemplate
		from langchain_core.output_parsers import StrOutputParser
		
		prompt = ChatPromptTemplate.from_template(
			"""
			Create a comprehensive executive summary of the meeting based on:
			
			- Transcript analysis
			- Action items identified
			- Sentiment analysis
			- Business insights
			
			Provide a clear, concise summary that highlights:
			1. Main discussion points
			2. Key decisions
			3. Action items and responsibilities
			4. Next steps
			5. Important insights or concerns
			
			Action Items: {action_items}
			Sentiment: {sentiment}
			Insights: {insights}
			
			Generate a professional executive summary.
			"""
		)
		
		chain = prompt | self.agent.llm | StrOutputParser()
		summary = chain.invoke({
			"action_items": action_items,
			"sentiment": sentiment,
			"insights": insights
		})
		
		state["summary"] = summary
		return state
	
	def run_meeting_analysis(self, transcript: str) -> dict:
		"""
		Run the complete meeting analysis workflow.
		
		Args:
			transcript: Meeting transcript text
		
		Returns:
			Dictionary with analysis results and summary
		"""
		workflow = self.create_meeting_analysis_workflow()
		app = workflow.compile()
		
		initial_state = {
			"data": {"transcript": transcript},
			"analysis_results": {},
			"summary": "",
			"emails": [],
			"email_analysis": [],
			"drafts": [],
			"email_database": {},
			"email_analysis_results": {},
			"email_visualizations": {},
			"email_summary": ""
		}
		
		final_state = app.invoke(initial_state)
		
		return {
			"summary": final_state["summary"],
			"analysis_results": final_state["analysis_results"],
			"action_items": final_state["analysis_results"].get("action_items", []),
			"sentiment": final_state["analysis_results"].get("sentiment", {}),
			"insights": final_state["analysis_results"].get("insights", {})
		}



