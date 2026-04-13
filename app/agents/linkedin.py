from agent_types import AgentRequest, AgentResponse
import { openai } from '@ai-sdk/openai';
import { streamText } from 'ai';

export async function linkedInAgent(
	request: AgentRequest
): Promise<AgentResponse> {
	// TODO: Implement the LinkedIn agent
	//
	// Follow Module 8 in the curriculum:
	//   1. Get the fine-tuned model ID from environment
	//   2. Build a system prompt for LinkedIn content
	//   3. Use streamText() to stream the response

	throw new Error('LinkedIn agent not implemented yet!');