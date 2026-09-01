# Test Analysis & Design JSON truncation fix

The runtime previously retried a malformed/truncated LLM response by feeding the truncated assistant payload back into the conversation. Large proposal output could then hit the output-token limit again and abort the entire Jira batch.

The fix:
- detects `stop_reason=max_tokens` explicitly;
- increases the bounded output budget from 3500/5000 to 6000/9000 tokens;
- retries from the original semantic input rather than continuing from malformed JSON;
- asks the retry to return a smaller complete JSON object without reproducing dataset records;
- reports malformed/truncated JSON clearly;
- isolates failures per Jira issue so one failed story does not erase successful results from other eligible stories;
- adds regression tests for fenced valid JSON and truncated invalid JSON.
