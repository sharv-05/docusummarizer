# Evaluation and manual rubric

Run `python -m docusummarizer.evaluation` to generate ROUGE-1, ROUGE-2, and ROUGE-L scores over the five sample transcripts. The sample runner uses a short reference brief as a repeatable smoke metric; replace the reference strings with expert gold summaries for a meaningful benchmark.

Manual rubric (1–5 each):

| Dimension | 1 | 3 | 5 |
|---|---|---|---|
| Attribution | Speaker missing or wrong | Partial attribution | Decisions/actions consistently attributed |
| Completeness | Major items absent | Most major items present | Decisions, owners, deadlines, risks covered |
| Actionability | Vague notes | Some usable next steps | Clear task, owner, deadline, status |
| Faithfulness | Hallucinations | Minor ambiguity | Every claim traceable to transcript |
