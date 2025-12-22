"""3-stage LLM Council orchestration."""

from typing import List, Dict, Any, Tuple
from .openrouter import query_models_parallel, query_model
from .config import COUNCIL_MODELS, CHAIRMAN_MODEL
from .pricing import calculate_cost


async def stage1_collect_responses(
    messages: List[Dict[str, str]],
    council_models: List[str],
    model_personas: Dict[str, str] = None
) -> List[Dict[str, Any]]:
    """
    Stage 1: Collect individual responses from all council models.

    Args:
        messages: Full conversation history
        council_models: List of model identifiers
        model_personas: Optional mapping of model ID to system prompt/persona

    Returns:
        List of dicts with 'model' and 'response' keys
    """
    import asyncio
    
    # Create tasks for each model
    tasks = []
    
    for model in council_models:
        # Clone messages to avoid modifying the original list for other models
        model_messages = list(messages)
        
        # Inject persona if available
        if model_personas and model in model_personas:
            persona = model_personas[model]
            # Prepend as system message
            # Note: Some models might not support system messages, but OpenRouter usually handles this
            # or we could use 'reasoning.py' helpers to check.
            # For simplicity, we prepend a system message.
            model_messages.insert(0, {"role": "system", "content": persona})
            
        tasks.append(query_model(model, model_messages))

    # Wait for all to complete
    responses_list = await asyncio.gather(*tasks)
    
    # Map back to model names
    responses = {model: response for model, response in zip(council_models, responses_list)}

    # Format results
    stage1_results = []
    for model, response in responses.items():
        if response is not None:
            usage = response.get('usage', {})
            cost = calculate_cost(
                model,
                usage.get('prompt_tokens', 0),
                usage.get('completion_tokens', 0)
            )

            result_entry = {
                "model": model,
                "response": response.get('content', ''),
                "thinking": response.get('thinking', ''),
                "is_reasoning_model": response.get('is_reasoning_model', False),
                "usage": usage,
                "cost": cost,
                "persona": model_personas.get(model) if model_personas else None
            }
            
            if response.get('error'):
                result_entry['error'] = response['error']
                
            stage1_results.append(result_entry)

    return stage1_results


async def extract_ranking_with_llm(ranking_text: str, labels: List[str]) -> List[str]:
    """
    Use a fast LLM to extract the ranking if regex parsing fails.
    """
    labels_str = ", ".join(labels)
    prompt = f"""You are a data extraction assistant. I have a text where an AI model evaluated several responses (labeled {labels_str}).
I need you to extract the final ranking the model decided on.

Evaluation Text:
{ranking_text}

Task:
1. Identify the final ranking of the responses from best to worst.
2. Return ONLY the labels in order, separated by commas.
3. Use the exact labels provided: {labels_str}

Example output: Response C, Response A, Response B

Final Ranking:"""

    messages = [{"role": "user", "content": prompt}]
    
    # Use a fast, cheap model for extraction (same as title generation)
    response = await query_model("google/gemini-2.5-flash", messages, timeout=20.0)
    
    if not response:
        return []
        
    content = response.get('content', '').strip()
    
    import re
    # Extract labels from the response
    found_labels = []
    for label in labels:
        if label in content:
            found_labels.append(label)
            
    # Sort found labels by their position in the response to maintain order
    found_labels.sort(key=lambda l: content.find(l))
    
    return found_labels


def parse_ranking_from_text(ranking_text: str) -> List[str]:
    """
    Parse the FINAL RANKING section from the model's response using regex.

    Args:
        ranking_text: The full text response from the model

    Returns:
        List of response labels in ranked order
    """
    import re

    # Normalize text (handle common variations)
    text = ranking_text.replace("**", "") # Remove bolding which can mess up regex
    
    # Look for "FINAL RANKING:" section
    search_text = text
    if "FINAL RANKING:" in text:
        parts = text.split("FINAL RANKING:")
        if len(parts) >= 2:
            search_text = parts[-1]
    
    # Pattern 1: Numbered "Response X" (e.g., "1. Response A" or "1) Response A")
    numbered_matches = re.findall(r'\d+[\.\)]\s*(Response\s+[A-Z])', search_text, re.IGNORECASE)
    if numbered_matches:
        return [m.replace("Response", "Response ").replace("  ", " ").strip().title() for m in numbered_matches]

    # Pattern 2: Just "Response X" patterns in order
    matches = re.findall(r'Response\s+[A-Z]', search_text, re.IGNORECASE)
    if matches:
        # Deduplicate while preserving order
        seen = set()
        result = []
        for m in matches:
            normalized = m.replace("Response", "Response ").replace("  ", " ").strip().title()
            if normalized not in seen:
                result.append(normalized)
                seen.add(normalized)
        return result

    # Pattern 3: If in FINAL RANKING section, look for single letters
    if "FINAL RANKING:" in text:
        letters = re.findall(r'\d+[\.\)]\s*([A-Z])(?!\w)', search_text)
        if letters:
            return [f"Response {l}" for l in letters]

    return []


async def stage2_collect_rankings(
    user_query: str,
    stage1_results: List[Dict[str, Any]],
    council_models: List[str]
) -> Tuple[List[Dict[str, Any]], Dict[str, str]]:
    """
    Stage 2: Each model ranks the anonymized responses.

    Args:
        user_query: The original user query
        stage1_results: Results from Stage 1
        council_models: List of model identifiers

    Returns:
        Tuple of (rankings list, label_to_model mapping)
    """
    # Create anonymized labels for responses (Response A, Response B, etc.)
    labels = [f"Response {chr(65 + i)}" for i in range(len(stage1_results))]

    # Create mapping from label to model name
    label_to_model = {
        label: result['model']
        for label, result in zip(labels, stage1_results)
    }

    # Build the ranking prompt
    responses_text = "\n\n".join([
        f"{label}:\n{result['response']}"
        for label, result in zip(labels, stage1_results)
    ])

    ranking_prompt = f"""You are evaluating different responses to the following question:

Question: {user_query}

Here are the responses from different models (anonymized):

{responses_text}

Your task:
1. First, evaluate each response individually. For each response, explain what it does well and what it does poorly.
2. Then, at the very end of your response, provide a final ranking.

IMPORTANT: Your final ranking MUST be formatted EXACTLY as follows:
- Start with the line "FINAL RANKING:" (all caps, with colon)
- Then list the responses from best to worst as a numbered list
- Each line should be: number, period, space, then ONLY the response label (e.g., "1. Response A")
- Do not add any other text or explanations in the ranking section

Example of the correct format for your ENTIRE response:

Response A provides good detail on X but misses Y...
Response B is accurate but lacks depth on Z...
Response C offers the most comprehensive answer...

FINAL RANKING:
1. Response C
2. Response A
3. Response B

Now provide your evaluation and ranking:"""

    messages = [{"role": "user", "content": ranking_prompt}]

    # Get rankings from all council models in parallel
    responses = await query_models_parallel(council_models, messages)

    # Format results
    stage2_results = []
    for model, response in responses.items():
        if response is not None:
            full_text = response.get('content', '')
            
            # Step 1: Try regex parsing
            parsed = parse_ranking_from_text(full_text)
            
            # Step 2: Fallback to LLM extraction if regex failed to find all responses
            # We expect parsed to have the same number of items as stage1_results
            # Only run extraction if there is actual content and no error
            if not response.get('error') and len(parsed) < len(stage1_results):
                llm_parsed = await extract_ranking_with_llm(full_text, labels)
                if len(llm_parsed) >= len(parsed):
                    parsed = llm_parsed

            usage = response.get('usage', {})
            cost = calculate_cost(
                model,
                usage.get('prompt_tokens', 0),
                usage.get('completion_tokens', 0)
            )

            result_entry = {
                "model": model,
                "ranking": full_text,
                "thinking": response.get('thinking', ''),
                "is_reasoning_model": response.get('is_reasoning_model', False),
                "parsed_ranking": parsed,
                "usage": usage,
                "cost": cost
            }

            if response.get('error'):
                result_entry['error'] = response['error']

            stage2_results.append(result_entry)

    return stage2_results, label_to_model


async def stage2_5_rebuttal(
    user_query: str,
    stage1_results: List[Dict[str, Any]],
    stage2_results: List[Dict[str, Any]],
    label_to_model: Dict[str, str],
    model_personas: Dict[str, str] = None
) -> List[Dict[str, Any]]:
    """
    Stage 2.5: Rebuttal Round. Models see critiques and can update their answers.

    Args:
        user_query: Original user question
        stage1_results: Original answers
        stage2_results: Peer rankings and critiques
        label_to_model: Mapping of labels to model names
        model_personas: Optional personas

    Returns:
        List of updated stage1-like results (or original if no update)
    """
    # Create mapping of model -> critique text received
    model_critiques = {result['model']: [] for result in stage1_results}
    
    # Invert the rankings to gather critiques FOR each model
    # stage2_results contains what each model SAID about others
    for ranking_result in stage2_results:
        reviewer_model = ranking_result['model']
        critique_text = ranking_result['ranking']
        
        # We need to extract the specific critique for each model if possible
        # Since the full text contains all critiques, we'll just pass the full text 
        # and let the model find the section about itself.
        # Ideally, we would parse this better, but passing full context is safer.
        for label, target_model in label_to_model.items():
            if target_model in model_critiques:
                model_critiques[target_model].append(
                    f"Critique from Peer ({reviewer_model}):\n{critique_text}"
                )

    # Prepare rebuttal tasks
    import asyncio
    tasks = []
    participating_models = []

    for result in stage1_results:
        model = result['model']
        original_response = result['response']
        critiques = "\n\n---\n\n".join(model_critiques.get(model, []))
        
        if not critiques:
            continue

        participating_models.append(model)
        
        # Identify which label this model was
        my_label = next((l for l, m in label_to_model.items() if m == model), "Unknown")

        rebuttal_prompt = f"""You previously answered a user question. Other AI models have now reviewed and ranked all answers, including yours (you are identified as {my_label}).

Original Question: {user_query}

Your Original Answer:
{original_response}

---
PEER REVIEWS AND RANKINGS:
{critiques}
---

Your Task:
1. Read the critiques of your specific answer ({my_label}).
2. Decide if you want to update or refine your answer based on valid points raised by peers.
3. If your original answer was perfect, just repeat it. If you missed something, fix it.
4. Provide your FINAL, revised answer. Do not include "Thinking" or meta-commentary about the process in the final output, just the answer.

Revised Answer:"""

        messages = [{"role": "user", "content": rebuttal_prompt}]
        
        # Inject persona if available
        if model_personas and model in model_personas:
            messages.insert(0, {"role": "system", "content": model_personas[model]})

        tasks.append(query_model(model, messages))

    if not tasks:
        return stage1_results

    # Run rebuttals in parallel
    rebuttal_responses = await asyncio.gather(*tasks)
    
    # Merge results
    updated_results = []
    rebuttal_map = {model: resp for model, resp in zip(participating_models, rebuttal_responses)}

    for result in stage1_results:
        model = result['model']
        if model in rebuttal_map and rebuttal_map[model] and not rebuttal_map[model].get('error'):
            new_response = rebuttal_map[model]
            
            # Combine costs
            original_usage = result.get('usage', {})
            new_usage = new_response.get('usage', {})
            
            combined_usage = {
                'prompt_tokens': original_usage.get('prompt_tokens', 0) + new_usage.get('prompt_tokens', 0),
                'completion_tokens': original_usage.get('completion_tokens', 0) + new_usage.get('completion_tokens', 0),
                'total_tokens': original_usage.get('total_tokens', 0) + new_usage.get('total_tokens', 0)
            }
            
            combined_cost = result.get('cost', 0) + calculate_cost(
                model, 
                new_usage.get('prompt_tokens', 0), 
                new_usage.get('completion_tokens', 0)
            )

            updated_results.append({
                "model": model,
                "response": new_response.get('content', result['response']), # Use new content
                "thinking": new_response.get('thinking', ''), # New thinking
                "is_reasoning_model": result['is_reasoning_model'],
                "usage": combined_usage,
                "cost": combined_cost,
                "persona": result.get('persona'),
                "is_rebuttal": True # Flag to indicate this is a revised answer
            })
        else:
            # Keep original
            updated_results.append(result)

    return updated_results


async def stage3_synthesize_final(
    user_query: str,
    stage1_results: List[Dict[str, Any]],
    stage2_results: List[Dict[str, Any]],
    chairman_model: str
) -> Dict[str, Any]:
    """
    Stage 3: Chairman synthesizes final response.

    Args:
        user_query: The original user query
        stage1_results: Individual model responses from Stage 1
        stage2_results: Rankings from Stage 2
        chairman_model: Model identifier for the chairman

    Returns:
        Dict with 'model' and 'response' keys
    """
    # Build comprehensive context for chairman
    stage1_text = ""
    for result in stage1_results:
        thinking_text = ""
        if result.get('thinking'):
            thinking_text = f"Thinking Process:\n{result['thinking']}\n\n"
        
        stage1_text += f"Model: {result['model']}\n{thinking_text}Response: {result['response']}\n\n"

    stage2_text = "\n\n".join([
        f"Model: {result['model']}\nRanking: {result['ranking']}"
        for result in stage2_results
    ])

    chairman_prompt = f"""You are the Chairman of an LLM Council. Multiple AI models have provided responses to a user's question, and then ranked each other's responses.

Original Question: {user_query}

STAGE 1 - Individual Responses:
{stage1_text}

STAGE 2 - Peer Rankings:
{stage2_text}

Your task as Chairman is to synthesize all of this information into a single, comprehensive, accurate answer to the user's original question. Consider:
- The individual responses and their insights
- The peer rankings and what they reveal about response quality
- Any patterns of agreement or disagreement

Provide a clear, well-reasoned final answer that represents the council's collective wisdom:"""

    messages = [{"role": "user", "content": chairman_prompt}]

    # Query the chairman model
    response = await query_model(chairman_model, messages)

    if response is None:
        # Fallback if chairman fails
        return {
            "model": chairman_model,
            "response": "Error: Unable to generate final synthesis.",
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            "cost": 0.0
        }

    usage = response.get('usage', {})
    cost = calculate_cost(
        chairman_model,
        usage.get('prompt_tokens', 0),
        usage.get('completion_tokens', 0)
    )

    return {
        "model": chairman_model,
        "response": response.get('content', ''),
        "thinking": response.get('thinking', ''),
        "is_reasoning_model": response.get('is_reasoning_model', False),
        "usage": usage,
        "cost": cost
    }


def calculate_aggregate_rankings(
    stage2_results: List[Dict[str, Any]],
    label_to_model: Dict[str, str]
) -> List[Dict[str, Any]]:
    """
    Calculate aggregate rankings across all models.

    Args:
        stage2_results: Rankings from each model
        label_to_model: Mapping from anonymous labels to model names

    Returns:
        List of dicts with model name and average rank, sorted best to worst
    """
    from collections import defaultdict

    # Track positions for each model
    model_positions = defaultdict(list)

    for ranking in stage2_results:
        # Use the pre-parsed ranking which includes fallback logic results
        parsed_ranking = ranking.get('parsed_ranking', [])
        
        # Fallback to re-parsing if missing (backward compatibility)
        if not parsed_ranking:
            parsed_ranking = parse_ranking_from_text(ranking['ranking'])

        for position, label in enumerate(parsed_ranking, start=1):
            if label in label_to_model:
                model_name = label_to_model[label]
                model_positions[model_name].append(position)

    # Calculate average position for each model
    aggregate = []
    for model, positions in model_positions.items():
        if positions:
            avg_rank = sum(positions) / len(positions)
            aggregate.append({
                "model": model,
                "average_rank": round(avg_rank, 2),
                "rankings_count": len(positions)
            })

    # Sort by average rank (lower is better)
    aggregate.sort(key=lambda x: x['average_rank'])

    return aggregate


async def generate_conversation_title(user_query: str) -> str:
    """
    Generate a short title for a conversation based on the first user message.

    Args:
        user_query: The first user message

    Returns:
        A short title (3-5 words)
    """
    title_prompt = f"""Generate a very short title (3-5 words maximum) that summarizes the following question.
The title should be concise and descriptive. Do not use quotes or punctuation in the title.

Question: {user_query}

Title:"""

    messages = [{"role": "user", "content": title_prompt}]

    # Use gemini-2.5-flash for title generation (fast and cheap)
    response = await query_model("google/gemini-2.5-flash", messages, timeout=30.0)

    if response is None:
        # Fallback to a generic title
        return "New Conversation"

    title = response.get('content', 'New Conversation').strip()

    # Clean up the title - remove quotes, limit length
    title = title.strip('"\'')

    # Truncate if too long
    if len(title) > 50:
        title = title[:47] + "..."

    return title


async def run_full_council(
    messages: List[Dict[str, str]],
    council_models: List[str],
    chairman_model: str,
    model_personas: Dict[str, str] = None
) -> Tuple[List, List, Dict, Dict]:
    """
    Run the complete 3-stage council process.

    Args:
        messages: Full conversation history
        council_models: List of model identifiers
        chairman_model: Model identifier for the chairman
        model_personas: Optional mapping of model ID to system prompt/persona

    Returns:
        Tuple of (stage1_results, stage2_results, stage3_result, metadata)
    """
    # Extract the latest user query for Stage 2 and 3 context
    user_query = messages[-1]['content'] if messages else ""

    # Stage 1: Collect individual responses
    stage1_results = await stage1_collect_responses(messages, council_models, model_personas)

    # If no models responded successfully, return error
    if not stage1_results:
        return [], [], {
            "model": "error",
            "response": "All models failed to respond. Please try again."
        }, {}

    # Stage 2: Collect rankings
    stage2_results, label_to_model = await stage2_collect_rankings(user_query, stage1_results, council_models)

    # Calculate aggregate rankings
    aggregate_rankings = calculate_aggregate_rankings(stage2_results, label_to_model)

    # Stage 2.5: Rebuttal Round
    # Models get a chance to update their answers based on peer critiques
    stage2_5_results = await stage2_5_rebuttal(
        user_query,
        stage1_results,
        stage2_results,
        label_to_model,
        model_personas
    )

    # Stage 3: Synthesize final answer
    # Use the UPDATED (rebuttal) results for the final synthesis
    stage3_result = await stage3_synthesize_final(
        user_query,
        stage2_5_results,  # Pass revised answers
        stage2_results,
        chairman_model
    )

    # Calculate total cost
    total_cost = 0.0
    total_tokens = {"prompt": 0, "completion": 0, "total": 0}

    # Sum costs from all stages (use stage2_5_results as it includes stage 1 costs + rebuttal costs)
    for result in stage2_5_results:
        total_cost += result.get('cost', 0)
        usage = result.get('usage', {})
        total_tokens["prompt"] += usage.get('prompt_tokens', 0)
        total_tokens["completion"] += usage.get('completion_tokens', 0)
        total_tokens["total"] += usage.get('total_tokens', 0)

    for result in stage2_results:
        total_cost += result.get('cost', 0)
        usage = result.get('usage', {})
        total_tokens["prompt"] += usage.get('prompt_tokens', 0)
        total_tokens["completion"] += usage.get('completion_tokens', 0)
        total_tokens["total"] += usage.get('total_tokens', 0)

    total_cost += stage3_result.get('cost', 0)
    usage = stage3_result.get('usage', {})
    total_tokens["prompt"] += usage.get('prompt_tokens', 0)
    total_tokens["completion"] += usage.get('completion_tokens', 0)
    total_tokens["total"] += usage.get('total_tokens', 0)

    # Prepare metadata
    metadata = {
        "label_to_model": label_to_model,
        "aggregate_rankings": aggregate_rankings,
        "total_cost": round(total_cost, 4),
        "total_tokens": total_tokens
    }

    return stage2_5_results, stage2_results, stage3_result, metadata