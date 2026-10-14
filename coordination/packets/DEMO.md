# Estimator Comparison Evidence Packet

Packet ID: `P001`. Public synthetic material only; this packet does not establish a real-world scientific finding.

This packet contains no real research results, private data or external references.
Research question: In a synthetic contaminated normal distribution, is the sample median less sensitive to outliers than the sample mean?
Proposed design: compare mean-squared error relative to the uncontaminated location 0, not the mixture mean 0.8. Use 100 observations per trial and 100 trials per scenario by default, with seed 42; the approved task is authoritative for exact parameters. A clean-normal N(0,1) baseline and a scenario with independent 10% probability of adding 8 are included. Within each trial both estimators use the same sample. Scenario samples are distinct. Record all parameters and the generator definition. The current demo does not compute confidence intervals or significance tests.
Known limitations: a toy simulation does not establish performance on real data; changing the contamination model may reverse conclusions; median can lose efficiency under a clean Gaussian model.
Review tasks: identify missing controls, uncertain claims, fair comparison rules and ways to reproduce the simulation. Do not invent numerical results. Do not claim to have run code.
