# IRSx Cookbook

This repository consists of a number of 'recipes' for using IRSx to achieve common tasks. Most recipes are present in their own notebook; some have additional dependencies beyond IRSx. The notebooks are styled to be readable rather than the model of exemplary python.

To run these as notebooks on your own machine, clone the repo, run `$ pip install -r requirements.txt` to install the requirements, and start a jupyter notebook with `$ jupyter notebook`.

IRSx docs are [here](https://github.com/jsfenfen/990-xml-reader#irsx); a variable reference is [here](http://irsx.info/).


# Recipes

#### Simple examples

1. [Get all the efilers from a city in a given year](https://github.com/jsfenfen/irsx_cookbook/blob/master/1.get_filers_from_year_city.ipynb)

2. [Print all schedule J salary records for the results of part 1](https://github.com/jsfenfen/irsx_cookbook/blob/master/2.simple_csv_output.ipynb)


#### Working examples





## Moving files around

IRSx will happily download files, one at a time, but if you've got millions consider whether there's a faster way. 

Amazon distributes a custom command line tool (AWS CLI) see more [here](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-welcome.html) that allows bulk copying and speeds up downloads, especially to another amazon bucket. It requires an Amazon password (Note that there's lots of ways of getting files from amazon, from FTP tools to s3 cmd too). There are [lotsa](https://stackoverflow.com/a/4721264) ways to do this.

## Other Repositories

IRSx is focused on reading xml forms using well-defined metadata; that metadata was *created* using [irs990_admin](https://github.com/jsfenfen/irs990_admin). The repo 
