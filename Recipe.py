# requester.py
import requests, re
from bs4 import BeautifulSoup
from fuzzywuzzy import fuzz
from fuzzywuzzy import process

class Recipe:

  # constructor takes in a link of a recipe from allRecipes.com
  def __init__(self, link):
    # web URL of the allRecipes link we are using in this instance of the Recipe
    self.link = link
    # list of ingredients
    self.ingredients = []
    # list of only names from the ingredients
    self.ingredient_names = []
    # list of the quantities of each ingredient
    self.quantities = []
    # list of values of the quantities, ie. integers or fractions
    self.quantity_values = []
    # list of directions from the webpage
    self.directions = []
    # dictionary of ingredients mapped to their quantities. Key: ingredient, Value: quantity
    self.mapping = {}
    # list of measurements retrieved from the quantities
    self.measurements = []
    # list of preparation key words
    self.preparation = []
    # list of descriptors of ingredients
    self.descriptors = []
    # dictionary of ingredients that can have low glycemic index replacements
    self.low_gi = {}
    # dictionary of ingredients that can have low sodium replacements
    self.low_sod = {}
    # dictionary of ingredients that can have vegetarian replacements
    self.veg = {}
    # dictionary of ingredients that can have pescatarian replacements
    self.pesc = {}
    # dictionary of ingredients that can have Italian cuisine replacements
    self.italian = {}
    # dictionary of ingredients that can have Asian cuisine replacements
    self.asian = {}

    self.transforms = {'low_gi':{}, 'low_sod':{}, 'veg':{},'pesc':{},'ita':{},'asi':{}}
    # GET the markup of the URL and store it as a member
    r = requests.get(link)
    self.markup = BeautifulSoup(r.text)

  # find all ingredients in markup and return a list of all of them (in order)
  def find_ingredients(self):
    elements = self.markup.select('.ingredient-name')
    arr = []
    for el in elements:
      arr.append(el.text)

    self.ingredients = arr
    return arr

  # get only the name of the ingredient from the list we get from the webscraper
  def find_ingredient_names(self):
    ings = self.find_ingredients()
    names = []
    for i in ings:
      if ',' in i:
        # split on comma
        words = i.split(",")
        for w in words:
          if len(w) == 1:
            names.append(w)
      else:
        words = i.split()
        names.append(words[len(words) - 1])

    self.ingredient_names = names
    return names

  # find all quantities in markup and return a list of all of them (in order)
  def find_quantities(self):
    elements = self.markup.select('.ingredient-amount')
    arr = []
    for el in elements:
      arr.append(el.text)

    self.quantities = arr
    return arr

  # returns a dictionary of each ingredient mapped to its associated quantity required
  def find_mapping(self):
    ingredients = self.find_ingredients()
    quantities = self.find_quantities()
    returnDict = {}
    if len(ingredients) != len(quantities):
      return {}
    for i in range(len(ingredients)):
      returnDict[ingredients[i]] = quantities[i]

    self.mapping = returnDict
    return returnDict

  # return the list of instructions on the webpage
  def find_directions(self):
    elements = self.markup.select('.directLeft')[0].find_all('li')
    arr = []
    for el in elements:
      arr.append(el.text)

    self.directions = arr
    return arr

  # find measurements from quantities
  def find_measurements(self):
    quantities = self.find_quantities()
    arr = []
    for el in quantities:
      words = el.split()
      for w in words:
        if '/' not in w and not w.isdigit():
          arr.append(w)

    self.measurements = arr
    return arr

  # return list of quantity values, ie. integers or fractions
  def find_quantity_values(self):
    quantities = self.find_quantities()
    values = []
    for q in quantities:
      words = q.split()
      val = ""
      if len(words) > 2:
        for w in words:
          if "/" in w or w.isdigit():
            val += w + " "
        values.append(val)
      else:
        values.append(words[0])

    self.quantity_values = values
    return values


  # parse descriptors (preparation and description)
  # def parse_preparation_descriptors(self):
  #   ingredients = self.find_ingredients()
  #   preparation = []
  #   descriptors = []
  #   for i in ingredients:
  #     words = i.split()
  #     match_obj = re.match('[a-z]{2,}((ed)|(nd))', i)
  #     if match_obj:
  #       match = match_obj.group()
  #       preparation.append(match)
  #     else:
  #       match = ''

  #     if len(words) == 2:
  #       if words[0] != match:
  #         descriptors.append(words[0])

  #     elif len(words) == 3:
  #       if words[0] == match:
  #         descriptors.append(words[1])
  #       elif words[1] == match:
  #         descriptors.append(words[0])


  #   self.preparation = preparation
  #   self.descriptors = descriptors
    
  # return preparation key words
  def find_preparation(self):
    ingredients = self.find_ingredients()
    prep = []
    for i in ingredients:
      words = i.split()
      match_obj = re.match('[a-z]{2,}((ed)|(nd))', i)
      if match_obj:
        match = match_obj.group()
      else:
        match = ''
      prep.append(match)

    self.preparation = prep
    return prep


  # return descriptors
  def find_descriptors(self):
    ingredients = self.find_ingredients()
    desc = []
    for i in ingredients:
      words = i.split()
      match_obj = re.match('[a-z]{2,}((ed)|(nd))', i)
      if match_obj:
        match = match_obj.group()
      else:
        match = ''
      
      if len(words) == 2:
        if words[0] != match:
          desc.append(words[0])
        else:
          desc.append("")

      elif len(words) == 3:
        if words[0] == match:
          desc.append(words[1])
        elif words[1] == match:
          desc.append(words[0])
        else:
          desc.append("")

      else:
        desc.append("")

    self.descriptors = desc
    return desc



  # return a dictionary of replacements based on the method from key
  # trans_dict: dictionary of replacements from appropriate csvs
  def transform(self, trans_dict, key):
    old = trans_dict.keys()
    new = {}
    ## Case by case removals
    ingreds = self.ingredients
    if key == 'low_gi' and 'water' in ingreds:
      ingreds.remove('water')
    for x in ingreds:
      for y in old:
        score = fuzz.partial_ratio(x, y)
        # if ingredient is in dictionary and the current replacement candidate is better than the stored replacement
        if x in new and score >= new[x][1]:
          # replace it
          new[x] = (trans_dict[y], score)
        # if ingredient is not in dictionary and the current replacement score is over 85, put it in
        elif not x in new and score >= 85:
          new[x] = (trans_dict[y], score)
    # take out scores
    for x in new.keys():
      new[x] = new[x][0]
    self.transforms[key] = new
    self.commit_transform(key)
    return new

  ## Changes directions
  def commit_transform(self,key):
    temp_dir = []
    for i, j in self.transforms[key].iteritems():
      for step in self.directions:
        temp_step = str(step)
        temp_dir.append(temp_step.replace(str(i),str(j)))
      self.directions = temp_dir
      temp_dir = []
      
      
      
      
      
      
        
        
      

# def main():
#   ex = Recipe("http://allrecipes.com/Recipe/Amish-Meatloaf/Detail.aspx?soid=carousel_0_rotd&prop24=rotd")
#   print ex.find_directions()

# if __name__ == '__main__':
#   main()
