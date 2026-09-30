# Research plan for Explainable AI in Intrusion Detection Systems

## Purpose and approval stage

This plan prepares an eight-page undergraduate research paper for the course AI Applications in Cyber Security. It contains the proposed outline, dataset, research gap, study design, and ten verified publications. The full paper will be drafted after approval, following the final instruction in the supplied prompt. No experiments have been run and no detection or explanation results are asserted here.

## Paper identity and template

**Title:** Explainable AI for Cybersecurity: Interpreting Machine Learning Decisions in Intrusion Detection Systems

**Authors in the supplied template:** Rajat Kumar and Sadhil Madan.

**Affiliation in the supplied template:** Information Technology, K. J. Somaiya School of Engineering.

**Template:** `IJSRP-paper-format.docx`. Its structure contains a full-width title and author block, a two-column body, numbered sections, and a reference section. The paper will retain its general typography and layout. The source template remains unchanged.

The template contains an incomplete ORCID for Sadhil Madan, sample reference entries, and example publication metadata including a placeholder DOI. These are drafting fields, not evidence that the paper has been published. The final draft should use only confirmed author identifiers and publication details. The course description in the prompt says AI & DS, whereas the author affiliation in the template says Information Technology; retain the supplied affiliation unless the authors correct it.

## Proposed dataset and scope

Use **UNSW-NB15** for a primary binary classification task: benign traffic versus attack traffic. Preserve the original attack categories separately for analysing which kinds of attacks are missed.

The dataset creators describe a mixture of real normal activities and synthetic attack behaviours, with nine attack categories. Their published partition contains **175,341 training records** and **82,332 testing records**. These are source dataset counts, not experimental results. The nine categories are Fuzzers, Analysis, Backdoors, DoS, Exploits, Generic, Reconnaissance, Shellcode, and Worms. [Official UNSW dataset description](https://research.unsw.edu.au/projects/unsw-nb15-dataset).

**Reason for selection:** The supplied training and testing partition makes a manageable, repeatable comparison possible within an undergraduate project. Mixed categorical and numeric network attributes also provide meaningful material for discussing how preprocessing affects explanations. Its age and laboratory generation limit conclusions about present-day production networks.

**Models:** Random Forest and XGBoost.

**Explanation methods:** SHAP for global and local feature attribution, with LIME as a second local explanation method.

**Research framing:** A comparative experimental study once implemented. Until then, the manuscript is a proposed-methodology paper with explicitly pending results.

## Research gap and proposed contribution

Applying SHAP or LIME to intrusion detection is established work. Arreche et al. compare explanation methods across multiple IDS models and datasets [6]. Gaspar et al. evaluate explanations using perturbations and participant feedback [7]. Mia et al. explicitly investigate false positives and false negatives through SHAP plots [8]. Hermosilla et al. compare SHAP and LIME on UNSW-NB15 with XGBoost and TabNet [9]. Consequently, the paper should not claim that explaining IDS errors or comparing SHAP and LIME is new.

**Proposed contribution:** A reproducible comparison of Random Forest and XGBoost on one fixed UNSW-NB15 evaluation protocol, examining detection quality alongside explanation agreement, stability, and processing time separately for correct and incorrect predictions. The analysis will connect influential attributes to network behaviour and document uncertainty when explanations disagree.

This is a scoped replication and extension of existing work. The value lies in the consistent protocol and the evidence produced, rather than a claim of a new learning or explanation algorithm. The broader motivation is the continuing need for standardised evaluation and practical explanation efficiency identified in the review by Mohale and Obagbuwa [10]. This gap statement is a synthesis of the selected literature, not proof that no other study has used the same configuration.

## Research questions

**Central question:** How effectively can Explainable AI techniques improve the interpretability of machine-learning-based intrusion detection systems while maintaining reliable intrusion-detection performance?

1. How do Random Forest and XGBoost compare in attack recall, false-positive rate, F1-score, and ROC-AUC under identical data partitions?
2. Which original network attributes most strongly influence each model, and how much do their feature rankings overlap?
3. How do SHAP and LIME explanations differ between true positives, true negatives, false positives, and false negatives?
4. How consistent are the explanations under repeated explanation runs and controlled changes to the background sample, and what is their computation cost?
5. What useful diagnostic observations can be made from error explanations, and which claims about analyst trust remain untested without a user study?

## Objectives

- Construct a documented preprocessing and training pipeline that prevents test data from influencing learned transformations or model selection.
- Compare the two models using the same evaluation records and clearly defined metrics.
- Generate global summaries and individual explanations using understandable network feature names.
- Analyse correctly detected attacks, correctly accepted normal traffic, false alarms, and missed attacks.
- Measure explanation agreement, sensitivity, and processing time, while distinguishing these measures from evidence of human understanding.

## Proposed eight-page outline

The allocations below total approximately eight pages, including references. Actual pagination will be checked in the supplied Word layout. The requested sections will remain identifiable, with related sections grouped under the template's major headings where appropriate.

| Approximate space | Sections and purpose |
|---|---|
| 0.5 page | **Title, Abstract, Keywords.** State the cybersecurity problem, models, dataset, explanation methods, and the actual status of implementation. |
| 0.6 page | **Introduction.** Explain why intrusion alerts need interpretable evidence and why both false alarms and missed attacks matter. |
| 1.1 pages | **Background / Related Work.** Define IDS and local/global explanation; include a compact literature comparison and synthesis. |
| 0.6 page | **Problem Statement, Research Gap, Research Questions, Objectives.** Establish the precise comparison and avoid unsupported novelty claims. |
| 0.9 page | **Proposed Methodology, Dataset Description.** Present the workflow, data partitioning, feature handling, and controls against information leakage. |
| 1.2 pages | **Implementation and Tools, Machine Learning Models Used, Explainable AI Techniques Used, Experimental Setup, Evaluation Metrics.** Make the study reproducible. |
| 1.6 pages | **Results and Analysis, Explainability Analysis, False Positive and False Negative Analysis.** Prioritise model comparison, global features, case studies, and explanation quality. Use pending tables until experiments exist. |
| 0.7 page | **Discussion, Limitations, Future Scope, Conclusion.** Interpret only supported findings and separate benchmark conclusions from deployment claims. |
| 0.8 page | **References.** Use numbered IEEE citations in order of first appearance. |

This outline covers all 24 sections requested in the supplied prompt. The final literature table, figures, and references must fit within the page budget; a short requirements checklist can accompany the paper separately.

## Proposed methodology

**Pipeline:** Network intrusion dataset → Data preprocessing → Feature selection → Model training → Intrusion prediction → Performance evaluation → SHAP and LIME → Interpretation → Analysis of true positives, true negatives, false positives, and false negatives → Model comparison → Conclusions.

### Data preparation

1. Obtain the official training and testing files and record file names, checksums, column definitions, and class counts. Audit duplicates and possible overlap between partitions. Report any departures from the supplied split explicitly.
2. Use the binary label as the target. Exclude the target, the attack-category label, and row identifiers from predictors. Keep the attack category only as evaluation metadata.
3. Use a validation portion within the training data for choosing settings. Keep the test data out of preprocessing fitting, feature selection, threshold selection, and parameter tuning.
4. Handle invalid numeric entries and missing values using a documented rule fitted on training data. Encode categorical attributes such as protocol, service, and state consistently, including a policy for unseen categories.
5. Remove constant features and investigate redundant attributes. If supervised feature selection is used, fit it only inside training folds and use the same selected feature set for both models. Retain a full-feature baseline to check whether selection changes detection performance.
6. Preserve the original test-set class distribution. If weighting or resampling is needed, apply it only to training data and record the configuration.

### Model training and evaluation

Use the same training/validation partitions and comparable tuning budgets for Random Forest and XGBoost. Record random seeds, final hyperparameters, software versions, and hardware. Use three stratified training folds as a practical starting point; group related or duplicate records when the data audit shows that independent row splitting is inappropriate.

Report a default probability threshold of 0.5 and, if needed, a second threshold chosen using validation data and a declared false-alarm objective. Do not select thresholds after inspecting the test results.

Treat attack as the positive class. Report accuracy, precision, recall, F1-score, confusion matrix, false-positive rate, and ROC-AUC. Add PR-AUC to describe performance under class imbalance. Include sample counts and, if feasible, bootstrap uncertainty intervals, with the limitation that related traffic records may violate independence assumptions.

### Explanation analysis

Use a training-derived reference sample for SHAP. Record the explainer, background size, feature-dependence assumptions, class being explained, and whether the output is a probability or a raw model score. Do not directly compare attribution magnitudes expressed in different units.

For LIME, perturb original categorical features through a valid preprocessing wrapper. Avoid independently perturbing one-hot columns into impossible categories. Recognise that independently varying valid features may still create unrealistic network records because traffic attributes are related.

Aggregate transformed features back to their original network attributes. Compute global summaries from a representative test sample. Use separate error-focused samples for analysis; do not present an artificially balanced error sample as representative of overall traffic.

Select a reproducible random sample of up to 50 records from each prediction outcome for each model, using all available records if fewer exist. Record actual counts and seed. Compare both models and both explainers on the same record identifiers where feasible, even if their outcome categories differ.

Measure top-five feature overlap with Jaccard similarity, rank agreement where appropriate, LIME's local surrogate fidelity, and median explanation time per record. Assess LIME stability across repeated seeds and SHAP sensitivity to background-sample changes. These are different sources of variation and should be labelled separately. Agreement between explainers is not proof of correctness.

Present individual cases with their true label, predicted label, score, influential features, and a cautious interpretation of the traffic behaviour. Feature attribution describes the model's decision; it does not establish the real-world cause of an attack.

### Performance and interpretability relationship

Post-hoc explanations do not change a fixed model's predictions. Therefore, simply adding SHAP or LIME should not be described as improving accuracy, recall, or false-positive rate. The immediate trade-off is explanation quality and usefulness versus computation cost.

Any explanation-guided change to features, model settings, or thresholds needs a separate validation-controlled experiment. Once test results have informed a redesign, those same test records cannot serve as an untouched final evaluation. Analyst trust or faster incident triage would require a user study; the planned benchmark alone cannot demonstrate those outcomes.

### Implementation tools

Python in Jupyter Notebook or Google Colab, with Pandas, NumPy, scikit-learn, XGBoost, SHAP, LIME, and Matplotlib. Record the actual package versions and available hardware when implementation begins. A versioned notebook should reproduce the model metrics, figures, selected case identifiers, and explanation settings.

## Planned results and figures

Every unimplemented results subsection will begin **“To be updated after implementation.”** Empty cells will use “Pending”; no illustrative performance numbers will be inserted.

| Model | Accuracy | Precision | Recall | F1 | FPR | ROC-AUC | PR-AUC |
|---|---|---|---|---|---|---|---|
| Random Forest | Pending | Pending | Pending | Pending | Pending | Pending | Pending | Pending |
| XGBoost | Pending | Pending | Pending | Pending | Pending | Pending | Pending | Pending |

Additional proposed tables:

- **Literature review:** authors/year, paper title, method, dataset, main finding, and limitation or relevance to the proposed study.
- **Explanation comparison:** model, explainer, outcome group, sample count, fidelity measure where applicable, top-five agreement, stability measure, and median time.
- **Error cases:** record identifier, actual label, predicted label, score, leading features, SHAP/LIME agreement, and diagnostic interpretation.
- **Missed attack categories:** category, number of attacks, false negatives, and recall for each model.

Suggested figures:

1. End-to-end methodology flowchart, which can be drawn before implementation.
2. Side-by-side confusion matrices and ROC/precision-recall curves, after implementation.
3. Global SHAP feature rankings for both models, after implementation.
4. Compact SHAP and LIME case panels covering correct detections, false alarms, and missed attacks, after implementation.

Choose a subset of these figures to maintain readable text within eight pages. The abstract and conclusion must reflect whether the paper presents a protocol or completed experiments.

## Ten verified references in IEEE format

Publication metadata was checked against publisher/proceedings pages, author-hosted research records, and publisher-deposited Crossref records. The list deliberately combines original method and dataset papers with seven IDS-focused publications. The explanatory notes identify how each reference will support the paper; they are not new experimental findings.

[1] N. Moustafa and J. Slay, “UNSW-NB15: A comprehensive data set for network intrusion detection systems (UNSW-NB15 network data set),” in *2015 Military Communications and Information Systems Conference (MilCIS)*, 2015, pp. 1–6, doi: [10.1109/MilCIS.2015.7348942](https://doi.org/10.1109/MilCIS.2015.7348942).

Use: establishes dataset origin and design. It is a benchmark source, not evidence that the proposed models generalise to current operational networks.

[2] M. T. Ribeiro, S. Singh, and C. Guestrin, “ ‘Why Should I Trust You?’: Explaining the predictions of any classifier,” in *Proceedings of the 22nd ACM SIGKDD International Conference on Knowledge Discovery and Data Mining*, 2016, pp. 1135–1144, doi: [10.1145/2939672.2939778](https://doi.org/10.1145/2939672.2939778).

Use: original LIME method, which approximates a classifier locally. Its text and image demonstrations motivate explanation use, but IDS-specific validity must be tested. [Author manuscript](https://arxiv.org/abs/1602.04938).

[3] S. M. Lundberg and S.-I. Lee, “A unified approach to interpreting model predictions,” in *Advances in Neural Information Processing Systems*, vol. 30, 2017. [Official proceedings](https://proceedings.neurips.cc/paper/2017/hash/8a20a8621978632d76c43dfd28b67767-Abstract.html).

Use: establishes SHAP's additive attribution framework and its theoretical properties. These properties do not establish that an intrusion prediction is correct or causally explained.

[4] S. Patil et al., “Explainable artificial intelligence for intrusion detection system,” *Electronics*, vol. 11, no. 19, Art. no. 3079, 2022, doi: [10.3390/electronics11193079](https://doi.org/10.3390/electronics11193079).

Use: evaluates decision trees, Random Forest, SVM, and voting with LIME on CICIDS2017. It provides an ensemble IDS precedent; the proposed paper will examine both explanation methods and separate error outcomes. Full authors: Shruti Patil, Vijayakumar Varadarajan, Siddiqui Mohd Mazhar, Abdulwodood Sahibzada, Nihal Ahmed, Onkar Sinha, Satish Kumar, Kailash Shaw, and Ketan Kotecha.

[5] F. Wei, H. Li, Z. Zhao, and H. Hu, “xNIDS: Explaining deep learning-based network intrusion detection systems for active intrusion responses,” in *32nd USENIX Security Symposium (USENIX Security 23)*, 2023, pp. 4337–4354. [Official proceedings and paper](https://www.usenix.org/conference/usenixsecurity23/presentation/wei-feng).

Use: handles input history and feature dependencies to explain deep IDS models and produce defence rules. Its evaluation of four deep IDS systems motivates measuring fidelity and stability and checking realistic feature relationships; it is not the same model comparison as the proposed study.

[6] O. Arreche, T. Guntur, and M. Abdallah, “XAI-IDS: Toward proposing an explainable artificial intelligence framework for enhancing network intrusion detection systems,” *Applied Sciences*, vol. 14, no. 10, Art. no. 4170, 2024, doi: [10.3390/app14104170](https://doi.org/10.3390/app14104170).

Use: compares SHAP and LIME across seven classification models on CICIDS2017, NSL-KDD, and RoEduNet-SIMARGL2021. It establishes that broad comparative XAI-IDS frameworks already exist. The proposed scope centres on a fixed UNSW-NB15 protocol and error-stratified analysis.

[7] D. Gaspar, P. Silva, and C. Silva, “Explainable AI for intrusion detection systems: LIME and SHAP applicability on multi-layer perceptron,” *IEEE Access*, vol. 12, pp. 30164–30175, 2024, doi: [10.1109/ACCESS.2024.3368377](https://doi.org/10.1109/ACCESS.2024.3368377).

Use: applies LIME and SHAP to an MLP using a generated version of ADFA-LD system-call data, with perturbation analysis and participant feedback. It supports evaluating explanations rather than displaying plots alone; system-call results do not directly establish effectiveness for tabular network-flow classifiers.

[8] M. Mia, M. M. A. Pritom, T. Islam, and K. Hasan, “Visually analyze SHAP plots to diagnose misclassifications in ML-based intrusion detection,” in *2024 IEEE International Conference on Data Mining Workshops (ICDMW)*, 2024, pp. 632–641, doi: [10.1109/ICDMW65004.2024.00088](https://doi.org/10.1109/ICDMW65004.2024.00088).

Use: compares SHAP patterns across correct predictions and errors using CIC-IoT2023, NF-UQ-NIDS-v2, and HIKARI-2021. Its visual case analysis directly informs the proposed false-positive/false-negative study. The proposed evaluation retains the original test class distribution and also compares LIME. [Author manuscript](https://arxiv.org/html/2411.02670v1).

[9] P. Hermosilla, S. Berríos, and H. Allende-Cid, “Explainable AI for forensic analysis: A comparative study of SHAP and LIME in intrusion detection models,” *Applied Sciences*, vol. 15, no. 13, Art. no. 7329, 2025, doi: [10.3390/app15137329](https://doi.org/10.3390/app15137329).

Use: compares SHAP and LIME for XGBoost and TabNet on UNSW-NB15, including explanation stability and fidelity. This is a close prior study and limits novelty claims. The proposed paper uses Random Forest as the comparison model and organises analysis by prediction outcome. [Institutional research record](https://publica.fraunhofer.de/entities/publication/4c3f0b6e-b9af-47c0-8341-f6398b8ccf85).

[10] V. Z. Mohale and I. C. Obagbuwa, “A systematic review on the integration of explainable artificial intelligence in intrusion detection systems to enhancing transparency and interpretability in cybersecurity,” *Frontiers in Artificial Intelligence*, vol. 8, Art. no. 1526221, 2025, doi: [10.3389/frai.2025.1526221](https://doi.org/10.3389/frai.2025.1526221).

Use: synthesises XAI-IDS literature and identifies challenges in standardisation, scalability, and practical explanation use. As a review, it supplies context rather than a directly comparable experimental dataset or new model result. [Publisher full text](https://www.frontiersin.org/journals/artificial-intelligence/articles/10.3389/frai.2025.1526221/full).

The final manuscript should also cite the original Random Forest and XGBoost papers when explaining the algorithms. Those method citations can supplement this initial set; IEEE reference numbering will be updated to follow first appearance.

## Requirements checklist

- [x] Topic remains tied to AI Applications in Cyber Security.
- [x] All requested sections are mapped into an approximately eight-page outline.
- [x] One public dataset, two models, and two explanation methods are proposed.
- [x] Research gap acknowledges closely related work.
- [x] Ten real publications and their bibliographic details are identified.
- [x] Detection metrics and explanation evaluation are both planned.
- [x] False positives, false negatives, and correct predictions are included.
- [x] No experimental numbers are fabricated.
- [ ] Approval of the proposed direction before full drafting.
- [ ] Implementation and genuine experimental results.
- [ ] Completed per-paper literature table after detailed full-text review.
- [ ] Final Word authoring and visual page-by-page verification.
- [ ] Final citation and similarity checks. Original paraphrasing can reduce copying, but a plagiarism percentage below 10% cannot be guaranteed without checking the completed paper in the institution's chosen system.
