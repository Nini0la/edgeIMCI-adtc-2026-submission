# EdgeIMCI Interaction Design — Retrieval, Assessment Bundles, and Conversational Depth

## Core Product Question

EdgeIMCI does not necessarily need to behave like a highly conversational chatbot.

The real product objective is closer to:

> **Help a frontline PHC worker retrieve and execute the correct local IMCI decision procedure with minimal cognitive and interaction cost.**

The UX should therefore be optimized for:

- fast retrieval of the relevant clinical procedure;
- low dependence on memorized IMCI knowledge;
- minimal repeated typing;
- preservation of clinical decision logic;
- clear acquisition of the observations that actually matter;
- safe escalation when urgent findings exist.

The objective is **not conversation for its own sake**.

---

## The Retrieval Framing

IMCI can be viewed partly as a large procedural knowledge base containing:

- conditions;
- observations;
- thresholds;
- branches;
- classifications;
- treatments;
- referral decisions;
- reassessment steps.

An experienced PHC worker who perfectly remembers IMCI effectively performs:

```text
clinical presentation
        ↓
retrieve relevant pathway
        ↓
remember required questions / observations
        ↓
collect evidence
        ↓
follow branch
        ↓
classification + action
```

EdgeIMCI can act as **externalized procedural memory**.

The important retrieval target may therefore not simply be the final answer.

It may be:

> **the smallest useful piece of the decision procedure required to continue the assessment correctly.**

---

## Design Option A — Progressive Conversational Acquisition

Current information-policy work naturally supports an interactive loop:

```text
worker provides case
        ↓
EdgeIMCI identifies next required observation
        ↓
asks worker for it
        ↓
worker assesses / asks caregiver
        ↓
enters result
        ↓
EdgeIMCI recomputes
        ↓
repeat until decision sufficient
```

Example:

```text
Worker:
An 11-month-old child has fever.

EdgeIMCI:
Is the child able to drink or breastfeed?

Worker:
Yes.

EdgeIMCI:
Has the child had convulsions during this illness?

...
```

### Advantages

- EdgeIMCI controls the information-acquisition sequence.
- Unknown information remains explicitly unknown.
- It can prevent premature classification.
- It can dynamically stop asking once the outcome is invariant.
- Complex branches can be navigated incrementally.
- Errors from workers skipping decision-relevant observations may be reduced.

### Disadvantages

- Repeated assess → type → wait → read loops may be slow.
- It may be frustrating during live patient interaction.
- A deep pathway could require many conversational turns.
- It risks optimizing for chatbot interaction rather than PHC workflow.

---

## Design Option B — Context-Specific Decision / Assessment Card

Instead of asking for one observation at a time, EdgeIMCI could retrieve a compact piece of the relevant decision tree.

Conceptually:

```text
clinical presentation
        ↓
retrieve relevant local procedure
        ↓
display required checks + local branches
        ↓
worker performs assessment
        ↓
worker may act directly or return findings to EdgeIMCI
```

This resembles a dynamically generated **IMCI flash card** or **local decision card**.

However, the card must be self-contained.

Bad:

> Check for general danger signs.

This assumes the PHC worker already remembers what the danger signs are.

Better:

> Check the following general danger signs:
> - ask whether the child can drink or breastfeed;
> - ask whether the child vomits everything;
> - ask whether the child has had convulsions;
> - observe whether the child is lethargic or unconscious;
> - observe whether the child is convulsing now.

The system should retrieve the actual knowledge required to traverse the branch, not merely the name of the branch.

### Advantages

- Much less repeated interaction.
- The worker can perform several related checks together.
- Better suited to working face-to-face with a caregiver and child.
- Reduces reliance on memorized IMCI content.
- More closely resembles a practical clinical job aid.

### Disadvantages

- Too much information risks recreating the original handbook problem.
- Complex local decision trees may still become cumbersome.
- The worker may misapply the branch without returning findings to EdgeIMCI.
- Determining how much of the tree to reveal is itself a design problem.

---

## Design Option C — Assessment Bundles

A likely middle ground is to use the existing information-policy machinery to retrieve a **bundle of next useful acquisitions**.

Instead of:

```text
one observation
→ one response
→ one observation
→ one response
```

EdgeIMCI could produce:

```text
current state
        ↓
determine decision-relevant unknowns
        ↓
group safely obtainable observations
        ↓
display compact assessment bundle
        ↓
worker returns findings together
        ↓
recompute
```

Example:

> **Check these next:**
>
> Ask the caregiver whether the child:
> - can drink or breastfeed;
> - vomits everything;
> - has had convulsions.
>
> Observe whether the child:
> - is lethargic or unconscious;
> - is convulsing now.
>
> Enter the findings together when complete.

This could reduce a long pathway to only a few interactions.

Potential interaction shape:

```text
presentation
    ↓
assessment bundle
    ↓
worker performs several checks
    ↓
results entered together
    ↓
classification / next bundle / urgent action
```

This may provide most of the safety benefits of interactive acquisition without requiring excessive chat turns.

---

# Central UX Principle

The key optimization target should be:

> **Minimize what the PHC worker must retrieve from memory while also minimizing unnecessary interaction with the AI system.**

This creates two failure modes.

### Too little information

> “Check for danger signs.”

The worker must already know the guideline.

### Too much information

> Entire IMCI pathway or page.

The system recreates the original retrieval burden.

### Desired middle

> **The smallest self-contained decision fragment that lets the PHC worker correctly perform the next useful assessment without relying on omitted guideline knowledge.**

This is a candidate design principle for EdgeIMCI.

---

# Relationship to the Existing Information Policy

The information policy already computes much of what this UX requires:

```text
known evidence
        ↓
unknown evidence
        ↓
possible valid completions
        ↓
what can still change classification/actions
        ↓
decision-directed acquisitions
        ↓
assessment-completion acquisitions
```

Originally these outputs were interpreted mainly as:

> What question should the chatbot ask next?

A broader interpretation is:

> **What procedural information does the worker need next?**

The information-policy layer could therefore support multiple renderings of the same semantic state:

```text
state
 ├── conversational question
 ├── batched acquisition request
 └── compact assessment / decision card
```

This means the underlying clinical and information-policy architecture does not necessarily need to change if the preferred UX changes.

The **rendering contract** may change instead.

---

# Important Design Decisions Still Open

## 1. What is EdgeIMCI's default interaction unit?

Candidates:

- one question at a time;
- one acquisition bundle at a time;
- one local decision-tree fragment at a time.

This should be determined experimentally rather than assumed.

---

## 2. How much knowledge should each response expose?

The system must decide how far ahead to reveal the procedure.

Possible policies:

- only the immediately required observations;
- all observations required before the next classification boundary;
- the complete local subtree;
- adaptive amount based on pathway complexity.

---

## 3. Does the PHC worker need to return all findings to EdgeIMCI?

Two product models are possible.

### AI-mediated decision

The worker enters findings and EdgeIMCI performs the classification.

```text
assessment card
→ findings returned
→ EdgeIMCI classifies
```

### AI-assisted procedural retrieval

EdgeIMCI retrieves the relevant procedure and the worker applies it independently.

```text
assessment card
→ worker executes procedure
→ possibly no further AI interaction
```

The second model reduces interaction but places more procedural interpretation on the worker.

---

## 4. Should multiple UX modes exist?

Possible modes could eventually include:

- **Guided mode:** step-by-step acquisition.
- **Quick assessment mode:** batched observations.
- **Reference mode:** compact local decision card.

It may be unnecessary to force one interface philosophy across every clinical situation.

---

## 5. How should urgent findings change the interaction?

Urgent findings should probably override normal optimization for minimal turns.

When a known danger sign establishes an urgent action:

```text
urgent action
        ↓
display immediately
```

The system can separately indicate any remaining assessment information if clinically appropriate.

Urgent action must not be buried inside a long retrieved procedure.

---

# Key Experiment Needed

Before deciding the preferred interaction model, examine the actual structure of the clinical pathways.

Important measurements include:

- typical pathway depth;
- branching factor;
- number of decision-relevant acquisitions from common initial presentations;
- number of acquisitions that can safely be batched;
- proportion of cases resolved after one bundle;
- proportion requiring multiple sequential branches.

For example:

> If most common presentations require only 2–4 decision-relevant observations, conversational acquisition may be perfectly usable.

But:

> If common pathways require 10–15 observations across several conditional branches, assessment bundles or local decision cards become substantially more attractive.

The larger IMCI graph may later help quantify this.

---

# Implication for Training Data

The UX decision directly affects what behavior the model should learn.

Current assumed target:

```text
state
→ conversational next question
```

Possible richer target:

```text
state
→ compact next-assessment bundle
```

Or both:

```text
state + interaction mode
        ↓
appropriate rendering
```

Therefore the golden rendering and teacher-generation work should avoid prematurely assuming that the most conversational output is necessarily the best output.

The desired language should be judged by:

- procedural usefulness;
- clinical faithfulness;
- cognitive load;
- number of interactions required;
- memorization burden;
- clarity of next action.

Naturalness remains important, but it is not the primary objective.

---

# Current Working Hypothesis

A promising default is:

> **Situation → compact self-contained assessment bundle → findings returned together → classification/action or next bundle.**

This could preserve EdgeIMCI's deterministic information-policy advantages while reducing the need for repeated chat turns.

The hypothesis should remain open until pathway depth and real PHC workflow are examined.

---

# Design Principle to Retain

> **EdgeIMCI should retrieve enough of the local IMCI procedure that the PHC worker does not need to remember omitted clinical rules, but no more than is useful for the immediate decision.**
