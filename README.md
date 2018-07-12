## Nexis Parse

Description
===========

Breaks up a LexisNexis exported HTML file into clean individual text files and creates a CSV file with date (and other meta content). Each record in the CSV file is a separate article from the original LexisNexis output. 

Example Usage
===========
First import the required items. Because the package uses dataframes, you should import pandas. 
```python
from  nexisParse import *
```

Use `lexisParse` to disaggregate the LexisNexis HTML output file into individual texts and remove HTML. This function takes two parameters:
- `srcPath` : the path to the folder that contains the LexisNexis HTML files
- `destPath` : the path to the folder where the function will output the disaggregated individual texts. 


```python
lexisParse(srcPath = 'nexisFileSrcPath', destPath = 'individualTextsOutputPah')
```


Use `extractContent` to put individual text files into a pandas dataframe. This function takes three parameters:
- `sourceDir` : the path to the folder that contains the individual texts (this is usually the `destPath` in the `lexisParse` function)
- `doStopWords` : boolean variable that removes stopwords if set to True
- `doLemm` : boolean variable that creates a column for lemmatized versions of the text if set to True

```python
df = extractContent('individualTextsOutputPah', doStopWords=False, doLemm=False)
```

To save the dataframe to a CSV file for later use, use the to_csv command:
```python
df.to_csv('TextData.csv', encoding="utf-8")
```

