"""Canonical injected text. Source IDs remain in structured payload, not headers."""
def serialize(items, messages):
    return '\n\n'.join(
        f"[evidence:{i+1};role:{messages[x['message_id']]['role']};start:{x['start']};end:{x['end']}]\n{x['text']}"
        for i,x in enumerate(items)
    )
