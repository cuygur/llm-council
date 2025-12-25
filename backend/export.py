"""Export utilities for conversations."""

from typing import Dict, Any, List
from datetime import datetime
import json


def export_to_markdown(conversation: Dict[str, Any]) -> str:
    """
    Export a conversation to Markdown format.

    Args:
        conversation: Full conversation object with messages

    Returns:
        Markdown string
    """
    lines = []

    # Header
    lines.append(f"# {conversation.get('title', 'Conversation')}")
    lines.append("")
    lines.append(f"**Date:** {conversation.get('created_at', 'Unknown')}")
    lines.append(f"**ID:** {conversation.get('id', 'Unknown')}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Messages
    for i, msg in enumerate(conversation.get('messages', []), 1):
        if msg['role'] == 'user':
            lines.append(f"## Message {i}: User")
            lines.append("")
            lines.append(msg['content'])
            lines.append("")

        elif msg['role'] == 'assistant':
            lines.append(f"## Message {i}: Council Response")
            lines.append("")

            # Stage 1: Individual Responses
            stage1 = msg.get('stage1', [])
            if stage1:
                lines.append("### Stage 1: Individual Responses")
                lines.append("")
                for response in stage1:
                    model_name = response.get('model', 'Unknown')
                    model_short = model_name.split('/')[-1] if '/' in model_name else model_name
                    lines.append(f"#### {model_short}")
                    lines.append("")
                    lines.append(response.get('response', ''))
                    lines.append("")

            # Stage 2: Peer Rankings
            stage2 = msg.get('stage2', [])
            metadata = msg.get('metadata', {})
            if stage2:
                lines.append("### Stage 2: Peer Rankings")
                lines.append("")

                # Aggregate rankings
                aggregate = metadata.get('aggregate_rankings', [])
                if aggregate:
                    lines.append("#### Aggregate Rankings")
                    lines.append("")
                    lines.append("| Rank | Model | Avg Score | Votes |")
                    lines.append("|------|-------|-----------|-------|")
                    for idx, agg in enumerate(aggregate, 1):
                        model_short = agg['model'].split('/')[-1] if '/' in agg['model'] else agg['model']
                        lines.append(f"| {idx} | {model_short} | {agg['average_rank']:.2f} | {agg['rankings_count']} |")
                    lines.append("")

                # Individual rankings
                for ranking in stage2:
                    model_name = ranking.get('model', 'Unknown')
                    model_short = model_name.split('/')[-1] if '/' in model_name else model_name
                    lines.append(f"#### {model_short}'s Evaluation")
                    lines.append("")
                    lines.append(ranking.get('ranking', ''))
                    lines.append("")

            # Stage 3: Final Synthesis
            stage3 = msg.get('stage3', {})
            if stage3:
                lines.append("### Stage 3: Final Answer")
                lines.append("")
                chairman = stage3.get('model', 'Unknown')
                chairman_short = chairman.split('/')[-1] if '/' in chairman else chairman
                lines.append(f"**Chairman:** {chairman_short}")
                lines.append("")
                lines.append(stage3.get('response', ''))
                lines.append("")

        lines.append("---")
        lines.append("")

    return "\n".join(lines)


def export_to_json(conversation: Dict[str, Any], pretty: bool = True) -> str:
    """
    Export a conversation to JSON format.

    Args:
        conversation: Full conversation object with messages
        pretty: Whether to pretty-print the JSON

    Returns:
        JSON string
    """
    if pretty:
        return json.dumps(conversation, indent=2, ensure_ascii=False)
    return json.dumps(conversation, ensure_ascii=False)


def export_to_html(conversation: Dict[str, Any]) -> str:
    """
    Export a conversation to HTML format (used for PDF generation).

    Args:
        conversation: Full conversation object with messages

    Returns:
        HTML string
    """
    html = []

    # HTML header with styling
    html.append("""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 900px;
            margin: 40px auto;
            padding: 20px;
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #4a90e2;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #34495e;
            margin-top: 30px;
            border-left: 4px solid #4a90e2;
            padding-left: 10px;
        }}
        h3 {{
            color: #4a90e2;
            margin-top: 20px;
        }}
        h4 {{
            color: #666;
            margin-top: 15px;
        }}
        .metadata {{
            color: #666;
            font-size: 14px;
            margin-bottom: 20px;
        }}
        .user-message {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid #4a90e2;
            margin: 20px 0;
        }}
        .assistant-section {{
            margin: 20px 0;
        }}
        .stage {{
            margin: 20px 0;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 8px;
        }}
        .stage1 {{
            border-left: 4px solid #3498db;
        }}
        .stage2 {{
            border-left: 4px solid #9b59b6;
        }}
        .stage3 {{
            border-left: 4px solid #27ae60;
            background: #f0fff0;
        }}
        .model-response {{
            background: white;
            padding: 15px;
            margin: 10px 0;
            border-radius: 6px;
            border: 1px solid #e0e0e0;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
        }}
        th, td {{
            padding: 10px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background: #4a90e2;
            color: white;
            font-weight: 600;
        }}
        tr:hover {{
            background: #f5f5f5;
        }}
        .separator {{
            border-top: 2px solid #ddd;
            margin: 30px 0;
        }}
        pre {{
            background: #f5f5f5;
            padding: 10px;
            border-radius: 4px;
            overflow-x: auto;
        }}
        code {{
            background: #f5f5f5;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
        }}
    </style>
</head>
<body>
""".format(title=conversation.get('title', 'Conversation')))

    # Title and metadata
    html.append(f"<h1>{conversation.get('title', 'Conversation')}</h1>")
    html.append('<div class="metadata">')
    html.append(f"<strong>Date:</strong> {conversation.get('created_at', 'Unknown')}<br>")
    html.append(f"<strong>ID:</strong> {conversation.get('id', 'Unknown')}")
    html.append('</div>')

    # Messages
    for i, msg in enumerate(conversation.get('messages', []), 1):
        if msg['role'] == 'user':
            html.append(f'<h2>Message {i}: User</h2>')
            html.append(f'<div class="user-message">{_escape_html(msg["content"])}</div>')

        elif msg['role'] == 'assistant':
            html.append(f'<h2>Message {i}: Council Response</h2>')
            html.append('<div class="assistant-section">')

            # Stage 1
            stage1 = msg.get('stage1', [])
            if stage1:
                html.append('<div class="stage stage1">')
                html.append('<h3>Stage 1: Individual Responses</h3>')
                for response in stage1:
                    model_name = response.get('model', 'Unknown')
                    model_short = model_name.split('/')[-1] if '/' in model_name else model_name
                    html.append('<div class="model-response">')
                    html.append(f'<h4>{model_short}</h4>')
                    html.append(f'<div>{_format_text_as_html(response.get("response", ""))}</div>')
                    html.append('</div>')
                html.append('</div>')

            # Stage 2
            stage2 = msg.get('stage2', [])
            metadata = msg.get('metadata', {})
            if stage2:
                html.append('<div class="stage stage2">')
                html.append('<h3>Stage 2: Peer Rankings</h3>')

                # Aggregate rankings
                aggregate = metadata.get('aggregate_rankings', [])
                if aggregate:
                    html.append('<h4>Aggregate Rankings</h4>')
                    html.append('<table>')
                    html.append('<tr><th>Rank</th><th>Model</th><th>Avg Score</th><th>Votes</th></tr>')
                    for idx, agg in enumerate(aggregate, 1):
                        model_short = agg['model'].split('/')[-1] if '/' in agg['model'] else agg['model']
                        html.append(f'<tr><td>{idx}</td><td>{model_short}</td><td>{agg["average_rank"]:.2f}</td><td>{agg["rankings_count"]}</td></tr>')
                    html.append('</table>')

                # Individual rankings
                for ranking in stage2:
                    model_name = ranking.get('model', 'Unknown')
                    model_short = model_name.split('/')[-1] if '/' in model_name else model_name
                    html.append('<div class="model-response">')
                    html.append(f'<h4>{model_short}\'s Evaluation</h4>')
                    html.append(f'<div>{_format_text_as_html(ranking.get("ranking", ""))}</div>')
                    html.append('</div>')
                html.append('</div>')

            # Stage 3
            stage3 = msg.get('stage3', {})
            if stage3:
                html.append('<div class="stage stage3">')
                html.append('<h3>Stage 3: Final Answer</h3>')
                chairman = stage3.get('model', 'Unknown')
                chairman_short = chairman.split('/')[-1] if '/' in chairman else chairman
                html.append(f'<p><strong>Chairman:</strong> {chairman_short}</p>')
                html.append(f'<div>{_format_text_as_html(stage3.get("response", ""))}</div>')
                html.append('</div>')

            html.append('</div>')

        html.append('<div class="separator"></div>')

    # HTML footer
    html.append("""
</body>
</html>
""")

    return "\n".join(html)


def _escape_html(text: str) -> str:
    """Escape HTML special characters."""
    return (text
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('"', '&quot;')
            .replace("'", '&#39;'))


def _format_text_as_html(text: str) -> str:
    """Format text with basic HTML formatting (preserve line breaks)."""
    # Escape HTML
    text = _escape_html(text)
    # Convert line breaks to <br>
    text = text.replace('\n', '<br>')
    return text
