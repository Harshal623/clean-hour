# Submitting with only the Colab notebook (no GitHub)

The notebook `notebooks/clean_hour_colab.ipynb` is self-contained. It has the write-up, all of our code, the data it needs (bundled inside it), the tests and the app. You do not need to submit the GitHub repository.

## Steps (about 20 minutes, mostly waiting for the run)
1. Go to https://colab.research.google.com and sign in. Choose **File > Upload notebook** and pick the file `clean_hour_colab.ipynb` (3.8 MB, in the `notebooks` folder of the project folder on your computer).
2. Click **Runtime > Run all**. It takes about 10 minutes. The last cell prints a public link to the live app (that link only works while the session is running).
3. When it finishes, check that there are no red error messages. Click **File > Save** so the results stay stored in the notebook.
4. Click **Share** (top right). Under General access choose **Anyone with the link** and set it to **Viewer**. Copy the link.
5. Open that link in a private (incognito) window. You should see the write-up at the top and the tables and charts further down. If you see them, the link works for judges.

## What to put in the form
- **Code Link:** the Colab link from step 4.
- **Write-up Link:** the same Colab link (the write-up is in the first cells). The brief lists a Google Doc, a GitHub README or a PDF/Word file as write-up options, so to be safe also use **Write-up File** to upload a PDF of the notebook: in Colab choose **File > Print**, then Save as PDF (the large data cell is collapsed, so the PDF stays short).
- **Demo Video Link:** your YouTube (Unlisted) or Drive link.
- Team names, schools and emails: type them on the form. They are not in the notebook, so Round 1 can be judged blind.
- Credits: the notebook's last section lists every data source, assumption, related paper and the AI tool (Claude Code). Paste the same list into the form's credits box (see `submission/FORM_ANSWERS.md`).

## If something goes wrong
- A red error in a cell: send me the text and the cell title.
- The run takes too long: the free Colab CPU is slow. Keep the tab open and let it finish.
- Judges can read the saved outputs without running anything, so saving the notebook after one full run (step 3) matters.
