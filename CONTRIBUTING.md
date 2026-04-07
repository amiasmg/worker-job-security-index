# Contributing to LLM J-Curves

Thanks for your interest in improving this model. The goal is to build better intuition for the horizontal economics of frontier AI — and the model will improve with more eyes on it.

## What we welcome

This is a toy model, and we know it. Contributions that sharpen its usefulness are especially welcome:

- **Model improvements** — better calibration of default parameters, more realistic growth curves, additional variables (e.g. inference cost trajectories, open-source competition effects, multi-product revenue mix)
- **UI/UX improvements** — clearer labeling, better chart readability, annotations that help users understand what they're seeing
- **Bug fixes** — anything that makes the math wrong or the interface confusing
- **New scenarios or presets** — named parameter sets that illustrate specific theses (e.g. "OpenAI bull case", "commoditization scenario")
- **Documentation** — clearer explanations of the variables and their real-world analogs

## What to keep in mind

The model is intentionally simple. Complexity that doesn't build intuition is not an improvement. Before adding variables or features, ask: does this help someone think more clearly about the economics, or does it just add noise?

## How to contribute

1. Fork the repository
2. Create a branch: `git checkout -b your-feature-name`
3. Make your changes
4. Test locally: `npm install && npm run dev`
5. Open a pull request with a brief description of what you changed and why

For significant changes to the model's structure or assumptions, open an issue first to discuss the approach.

## Running locally

```bash
npm install
npm run dev
```

The main component is in `src/`. The model logic and UI are colocated in the React component.

## Questions

Open an issue or start a discussion. We're interested in hearing how people are using the tool and what would make it more useful.
