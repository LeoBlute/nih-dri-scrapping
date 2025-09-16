import requests as rq
import csv
from bs4 import BeautifulSoup
from collections import defaultdict

class Table:
   def format_element_text(self, text):
      if text == 'NULL' or text == 'ND':
         return 'ND'
      else:
         text = text.replace(',', '')
         text = text.replace('*', '')
         return text

   def __init__(self, html_rows, categories):
      self.column_names = []
      self.columns_indexed = defaultdict(list)

      #Subtable is a subset of the first html table, it does not contain the 'column index'
      self.has_subtable = False

      #Most table have some rows that represent a category, Xx:Infants, Males..
      current_category = ''

      #Used to keep track of how many elements are supposed to be in a single row
      row_length = 0

      #Used for indexing, in the case of a subtable is found
      row_offset = 0

      #If a subtable is found, this will hold the index where the start of it is, in relation to html_rows
      row_index_found_subtable = 0

      #Remove some garbage that can polute the text
      for th in html_rows:
         for sup in th.find_all('sup'):
            sup.decompose()

      for html_row_i, html_row in enumerate(html_rows):
         #columns are of type 'th'
         html_columns = html_row.find_all('th')

         #There are only two cases which html columns are found in a row
         if len(html_columns) > 0:
            #Found a subtable
            if len(self.column_names) > 0:
               self.column_names.extend([c_name.get_text(strip=True) for c_name in html_columns])
               row_offset += row_length
               row_length += len(html_columns)
               self.has_subtable = True
               row_index_found_subtable = html_row_i
               break
            #This is for table c-5 only
            elif html_columns[0].get_text(strip=True) == '':
               continue
            else: #Found the start of the table
               self.column_names.extend([c_name.get_text(strip=True) for c_name in html_columns])
               row_length = len(html_columns)
               continue

         html_elements = html_row.find_all('td')
         html_elements_text = [e.get_text(strip=True) for e in html_elements]

         #Found category
         if html_elements_text[0] in categories:
            #Change current category
            current_category = html_elements_text[0]
            continue #There's no row elements in html row when it's a 'category' row

         #Add the elements for each corresponding column(indexed)
         for e_i, e in enumerate(html_elements):
            e_text = self.format_element_text(e.get_text(strip=True))
            colspan = int(e.get('colspan'))
            if e_i == 0:
               self.columns_indexed[e_i].append(current_category+' '+e_text)
            else:
               #Some html elements occupy more than one column
               for i in range(0, colspan):
                  self.columns_indexed[e_i+i].append(e_text)

      if self.has_subtable:
         for html_row_i, html_row in enumerate(html_rows[row_index_found_subtable:]):
            if len(html_row.find_all('th')) > 0:
               continue

            html_elements = html_row.find_all('td')
            html_elements_text = [
               self.format_element_text(e.get_text(strip=True))
               for e in html_elements
            ]

            #Subtables use blank rows with one element to represent the categories of the main table
            if len(html_elements) == 1:
               continue

            for e_i, e in enumerate(html_elements):
               e_text = self.format_element_text(e.get_text(strip=True))
               colspan = int(e.get('colspan'))

               #Some html elements occupy more than one column
               for i in range(0, colspan):
                  self.columns_indexed[e_i+i+row_offset].append(e_text)

   def validate(self):
      assert(len(self.columns_indexed) == len(self.column_names))
      for col in self.columns_indexed.values():
         assert(len(self.columns_indexed[0]) == len(col))


   def to_csv_file(self, name):

      self.validate()

      with open(name, mode="w", newline="") as file:
         writer = csv.writer(file)
         writer.writerow(self.column_names) #Header

         for i in range(0, len(self.columns_indexed[0])):
            #Convert columns format to row format
            row = [value[i] for value in self.columns_indexed.values()]

            writer.writerow(row)


page = rq.get('https://www.ncbi.nlm.nih.gov/books/NBK208874/')
page_data = BeautifulSoup(page.text, 'html.parser')

tables = page_data.find_all('div', class_='table')

categories = ['Infants', 'Children', 'Males', 'Females', 'Pregnancy', 'Lactation', 'Males, Females']

table_c1 = Table(tables[0].find_all('tr'), categories)
table_c2 = Table(tables[1].find_all('tr'), categories)
table_c3 = Table(tables[4].find_all('tr'), categories)
table_c4 = Table(tables[7].find_all('tr'), categories)
table_c5 = Table(tables[8].find_all('tr'), categories)
table_c6 =  Table(tables[10].find_all('tr')+tables[11].find_all('tr'), categories)
table_c7 =  Table(tables[12].find_all('tr'), categories)
table_c8 =  Table(tables[13].find_all('tr'), categories)
table_c9 =  Table(tables[14].find_all('tr'), categories)

table_c1.to_csv_file('estimated_average_requirements.csv')
table_c2.to_csv_file('recommended_intake_for_individuals_vitamins.csv')
table_c3.to_csv_file('recommended_intake_for_individuals_elements.csv')
table_c4.to_csv_file('recommended_intake_for_individual_macronutrients.csv')
table_c5.to_csv_file('acceptable_macronutrient_distribution_range.csv')
table_c6.to_csv_file('tolerable_intake_level_vitamins.csv')
table_c7.to_csv_file('tolerable_intake_level_elements.csv')
table_c8.to_csv_file('additional_macronutrient_recommendations.csv')
table_c9.to_csv_file('reference_values_for_nutrition_labeling.csv')
