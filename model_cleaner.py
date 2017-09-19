import requests, numpy, json, re
import pandas as pd
from pprint import pprint

access_token = 'XXXX' # replace with your own access token from github

request = requests.get("https://api.github.com", headers={'Authorization': 'token '+ access_token})
print str(request)

# get all files in the repository
request = requests.get("https://api.github.com/repos/llooker/bug_reproducer_nlml/contents", headers={'Authorization': 'token '+ access_token})

result = request.json()

models = []
bugs = []
shas = []

# only get model files
for file in result:
    if file['name'].find(".model.lkml") != -1:
        models.append(file['name'])
        shas.append(file['sha'])

# extract the bug number
for model in models:
    if re.match('(\d+)', model) is not None:
        bug = re.match('(\d+)', model).group(1)
        bugs.append(bug)
    else:
        bugs.append(-9)

# create dataframe with model name & bug number
data = {'model': models, 'bug': bugs, 'sha': shas}
df = pd.DataFrame(data=data)

# remove models without bug number
df = df[df.bug != -9]

bug_statusses = []

# check for each bug
for bug in df['bug']:
    request = requests.get("https://api.github.com/repos/looker/helltool/issues/" + str(bug),                             headers={'Authorization': 'token '+ access_token})
    result = request.json()

        # if we get something get the state
    if request.status_code == 200:
        bug_statusses.append(result['state'])
    else:
        bug_statusses.append('unknown')

# turn it into a series
statusses = pd.Series(bug_statusses)

# add it to the dataframe
df['status'] = statusses.values

df.to_csv('out.csv', index=False)

df.head()

bug_statusses = []

# get only closed bugs
df = df[df.status == 'closed']

# actually removing the files on my dev branch
devbranch = "dev-brecht-vermeire-ncy9"

for index, row in df.iterrows():
    payload = {"message": "cleanup of fixed bug: #" + row['bug'], "committer": {"name": "Brecht Vermeire", "email": "brecht@looker.com"}, "sha": row['sha'],
               "branch": devbranch\
                }

    request = requests.delete("https://api.github.com/repos/llooker/bug_reproducer_nlml/contents/" + str(row['model']), headers={'Authorization': 'token '+ access_token}, params=payload)

    print str(request)
