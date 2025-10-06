# Personality Perception Analysis - Test 2

## Model Personalities

| Trait | Alice | Bob |
|-------|-------|-----|
| Openness | -0.800 | 0.800 |
| Carefulness | -0.800 | -0.500 |
| Extraversion | 0.700 | 1.000 |
| Amicability | -1.000 | 0.000 |
| Neuroticism | -1.000 | 1.000 |

## Data Summary

- **Total responses**: 44
- **Alice responses**: 22
- **Bob responses**: 22

## Results Analysis

### Alice (n=22 responses)

| Trait | Model | Perceived | Variance | Distance | Accuracy |
|-------|-------|-----------|----------|----------|-----------|
| Openness | -0.800 | -0.068 | 0.052 | 0.732 | 26.8% |
| Carefulness | -0.800 | -0.341 | 0.151 | 0.459 | 54.1% |
| Extraversion | 0.700 | 0.364 | 0.129 | 0.336 | 66.4% |
| Amicability | -1.000 | 0.318 | 0.098 | 1.318 | 0.0% |
| Neuroticism | -1.000 | 0.341 | 0.105 | 1.341 | 0.0% |
| **AVERAGE** | - | - | - | **0.837** | **16.3%** |

**Key Insights:**
- Most accurately perceived trait: **Extraversion** (distance: 0.336)
- Least accurately perceived trait: **Neuroticism** (distance: 1.341)
- Overall perception accuracy: **16.3%**

### Bob (n=22 responses)

| Trait | Model | Perceived | Variance | Distance | Accuracy |
|-------|-------|-----------|----------|----------|-----------|
| Openness | 0.800 | 0.068 | 0.024 | 0.732 | 26.8% |
| Carefulness | -0.500 | -0.273 | 0.056 | 0.227 | 77.3% |
| Extraversion | 1.000 | -0.114 | 0.106 | 1.114 | 0.0% |
| Amicability | 0.000 | -0.443 | 0.091 | 0.443 | 55.7% |
| Neuroticism | 1.000 | 0.091 | 0.174 | 0.909 | 9.1% |
| **AVERAGE** | - | - | - | **0.685** | **31.5%** |

**Key Insights:**
- Most accurately perceived trait: **Carefulness** (distance: 0.227)
- Least accurately perceived trait: **Extraversion** (distance: 1.114)
- Overall perception accuracy: **31.5%**

## Visualization

The main comparison chart has been saved as:
- Static: `result-test-2.png`
- Interactive: `result-test-2.html`

The distribution analysis chart has been saved as:
- Static: `distributions-test-2.png`
- Interactive: `distributions-test-2.html`

The OCEAN spider/radar chart has been saved as:
- Static: `spider-test-2.png`
- Interactive: `spider-test-2.html`

---
*Generated on 2025-10-06 17:17:04*
