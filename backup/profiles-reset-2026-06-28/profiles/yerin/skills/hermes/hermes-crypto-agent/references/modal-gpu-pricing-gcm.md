# Modal.com GPU Pricing Reference

Updated: June 2025. Source: https://modal.com/pricing

## Resource Costs (Per Second Billing)

| GPU | VRAM | $/sec | $/hr | $/day |
|-----|------|-------|------|-------|
| Nvidia T4 | 16GB | $0.000164 | $0.59 | $14.16 |
| Nvidia A10 (A10G) | 24GB | $0.000306 | $1.10 | $26.40 |
| Nvidia A100 40GB | 40GB | $0.000583 | $2.10 | $50.40 |
| Nvidia A100 80GB | 80GB | $0.000694 | $2.50 | $60.00 |
| Nvidia H100 | 80GB | $0.001261 | $4.54 | $108.96 |

## Cost Multipliers

- **Preemptible**: 0.33x base (3x cheaper, can be killed)
- **Region selection**: 1.5-1.75x base
- **Non-preemptible**: 3x base

## Starter Plan ($30/mo free)

- 10 GPU concurrency limit
- 100 containers max
- 5 deployed crons
- 8 deployed endpoints
- 1 day log retention
- Up to 3 seats

## Budget Calculator

With $30/month free credit:
- T4 continuous: ~50 hours
- A10G continuous: ~27 hours
- A100 40GB continuous: ~14 hours
- T4 preemptible: ~150 hours (if available)

## Tips

- Per-second billing means you only pay for actual runtime
- Build time (cargo build) counts toward billing — use pre-built images when possible
- `keep_warm=1` keeps a container alive but only charges during active execution
- Monitor usage at https://modal.com/apps
