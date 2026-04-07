# LLM J-Curves

**An interactive simulator for the horizontal economics of frontier AI model companies.**

Live demo: [amiasmg.github.io/llm-jcurves](https://amiasmg.github.io/llm-jcurves)

---

## What is this?

Frontier AI companies like OpenAI and Anthropic are losing billions of dollars per year while trading at extraordinary valuations. Most people look at their income statements and see disaster. This tool helps you look at the right thing instead: the **horizontal economics** of each model generation.

The analogy comes from credit cards. A credit card company looks deeply unprofitable when it's growing fast — because every new account requires upfront acquisition cost and a loss provision. But each individual account, properly underwritten, is a highly profitable long-term investment. The vertical economics show a loss. The horizontal economics show a franchise.

LLM companies work the same way. Each model generation requires a large upfront training investment, followed by an inference revenue stream over the model's commercial lifespan. The question is not whether they're losing money. Of course they are. The question is whether each model generation earns back more than it costs — and whether the business compounds fast enough to fund the next generation without perpetual external capital.

This simulator — a "toy model" built to develop intuition, not produce precise forecasts — lets you adjust the key variables and watch the J-curve shape of each model generation's cumulative P&L.

---

## The Four Key Variables

| Variable | Description | Current Ballpark |
|---|---|---|
| **Inference margin** | Revenue retained after cost of serving outputs | 40–60% |
| **Model dominance window** | Months a model holds frontier position before being displaced | 6–18 months |
| **Revenue growth rate** | Annual pace of revenue growth during a model's reign | 80–200%+ |
| **Training cost multiplier** | How much more expensive each successive model is to train | 3–5x per generation |

The dominance window is the most underappreciated of these. Compressing it from 18 to 12 months can turn a self-funding business into one requiring a billion dollars in external capital — at the same growth rate and margin. The required growth rate scales nonlinearly: a 6-month window requires ~500% annual growth; 24 months requires only ~100–150%.

At roughly **80% annual revenue growth**, with current margin and training cost assumptions, each generation can approximately self-fund the next. Below 70%, the math starts requiring external capital at scale. Above 100%, the business becomes a genuine compounding machine.

---

## Background

This tool was built to accompany a research piece by [Amias Gerety](https://github.com/amiasmg) and the QED Investors team: *"The Training Treadmill: The Microeconomics of Scaling Laws and AI Adoption."*

The core insight: the analysts who will get AI right are those who can read a J-curve, not just an income statement.

---

## Running Locally

```bash
npm install
npm run dev
```

Requires Node.js. Built with [React](https://react.dev/) and [Vite](https://vitejs.dev/).

To build for production:

```bash
npm run build
```

To deploy to GitHub Pages:

```bash
npm run deploy
```

---

## Caveats

This is a toy model. It does not reflect the actual economics of OpenAI, Anthropic, Google, or any other company. Real numbers are messier, involve competitive dynamics, product mix, and organizational variables no spreadsheet can capture.

The purpose is to build intuition — to show how sensitive the self-funding thesis is to small changes in growth rate or dominance window, and to illustrate why frontier market position is worth so much. Use the sliders. Try the scenarios that worry you. Try the ones that excite you.

---

## License

MIT — see [LICENSE](LICENSE)

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md)
