# Information Marketplace - Setup Instructions

## Getting Your OpenAI API Key

1. Go to [OpenAI Platform](https://platform.openai.com/api-keys)
2. Sign in or create an account
3. Click "Create new secret key"
4. Copy the key (it starts with `sk-`)

## Setting Up the .env File

1. Create a `.env` file in the root directory of the project

2. Add your OpenAI API key:
   ```bash
   OPENAI_API_KEY=sk-proj-abc123...xyz789
   ```

3. Save the file

## Testing the Setup

Run the test script to verify everything is working:

```bash
conda activate wordplay
python -m info_marketplace.load_env
```

You should see:
```
✓ API key loaded successfully!
```

## Running a Test with Live API Calls

Once your API key is set up, test the LLM policy:

```bash
python -m info_marketplace.scout_llm_policy
```

This will:
- Make 2 live API calls to OpenAI (Phase 1 and Phase 2)
- Show raw LLM outputs
- Display parsed results
- Estimate token usage and costs
- Cost: ~$0.001-0.003 for this test

## Security Notes

- ✓ The `.env` file is already in `.gitignore` - your API key won't be committed to git
- ✓ Never share your API key publicly
- ✓ Rotate your key if you accidentally expose it

## Models Available

The code supports three GPT-5 family models:

| Model | Speed | Cost | Use Case |
|-------|-------|------|----------|
| `gpt-5.4-mini` | Fast | Low | Primary model for experiments |
| `gpt-5.4` | Medium | High | Frontier comparison |
| `gpt-5.4-nano` | Fastest | Lowest | Baseline testing |

All use `reasoning={"effort": "low"}` by default.

## Cost Estimates

With `gpt-5.4-mini` at reasoning effort "low":
- Per round (2 phases): ~$0.001-0.003
- Per full game (10 rounds, 4 agents): ~$0.08-0.24
- Per condition (20 trials): ~$1.60-4.80
- Full experiment (3 conditions × 3 models): ~$15-45

## Troubleshooting

### "API_ERROR: ..." in output
- Check your API key is correct in `.env`
- Verify you have API credits in your OpenAI account
- Check your internet connection

### "OPENAI_API_KEY environment variable not set"
- Make sure you edited `.env` and replaced the placeholder
- Restart your Python session after editing `.env`

### Rate limits
- Free tier: 3 requests/minute, 200 requests/day
- Tier 1: 500 requests/minute
- Use exponential backoff (already implemented in code)

## Optional: Install python-dotenv

For better .env handling (optional):
```bash
pip install python-dotenv
```

The code will automatically use it if installed, otherwise uses the built-in fallback parser.
