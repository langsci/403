# -*- coding: utf-8 -*-

import sys
import xml.etree.ElementTree as etree
import re

#CONSONANTS = 'bcdfghjkḱlĺmḿńǹŋpṕrŕsśtvwzʒ'
#ONSET = 'bcdfghjkḱlĺmḿńǹnŋpṕrŕsśtvwzʒGKŊʧʤ'
#CODAS = 'mnŋgklr'
#VOWELS = 'aAáÁàâãāãȁeéèẽēȅɛəiíìĩīȉɪoóòõṍȭōȍɔuúùũṹūȕʊnʊʊ́ɔɛɪ́ɪ̄ɛ̄ɪ́'#n
#SECONDGLYPHS = "mpbʃʒ $"
currentletter = 'x'

def hyphenate(s):
    return s
    ##p = "(?<=[%s])([%s])(?![%s])"%(VOWELS,CONSONANTS,SECONDGLYPHS)
    ##temporarily get rid off digraphs
    #mod = s
    #p = "([%s][%s]?)([%s][^%s ]?)([%s])"%(VOWELS,CODAS,ONSET,VOWELS,VOWELS)
    #mod = re.sub(p,r"\1\\-\2\3",mod)
    #return mod
    

def normalize(s):
      return s
  
def cmd(command, value, indent=0, escape_underscore=True):
    command = command.replace("-","").replace("_","")
    try:
        value = normalize(value)
        value = value.replace("#","\#")\
          .replace("&","\&")
        if escape_underscore:
          value = value.replace("_","\_")
    except AttributeError:
        pass
    return 0*' '+"\\%s{%s}%%"%(command, value) 

def hypercmd(command, anchor, value, indent=0):
  #value = value.replace("#","\#").replace("&","\&").replace("_","\_")
    value = normalize(value)
    return 0*' '+"\\hypertarget{%s}{}%%\n%s"%(anchor,cmd(command,value)) 
 
def fromtext(e, label):  
  try:
    el = e.find('.//%s'%label)
    result = "".join([x.strip() for x in el.itertext()])
    return result
  except AttributeError:
    return None
    
 
def fromformtext(e,label):
  return fromtext(e, "%s/form/text"%label)
  
def fromfieldformtext(e,field):
  return fromformtext(e,"field[@type='%s']"%field) 
    
    
    
def fromtagformtext(e,field):
  return fromformtext(e,"tag[@type='%s']"%field) 
      
      
def fromnoteformtext(e,field):
  return fromformtext(e,"note[@type='%s']"%field) 
  
def printsafe(e, field):
  value =  e.__dict__.get(field, False)
  if value:
    print(cmd(field, value))

def numbers_to_subscript(s):
  return re.sub("([0-9])",r"\\textsubscript{\1}",s)
 
class LexEntry():
    
    def __init__(self,e):

        global currentletter
        self.element = e
        self.ID = self.element.attrib.get('id', False)
        self.order = self.element.attrib.get('order', '')
        #self.citationform = fromformtext(self.element,"citation") #not needed for Shebro
        self.lexicalunit = fromformtext(self.element,"lexical-unit")
        self.firstletter = self.lexicalunit.replace('-','').lower().replace("ɡ",'g').replace("ɡ",'ǵ')[0]
        self.normalizedfirstletter = self.firstletter.replace('ɔ','o').replace('ɛ','e').replace('ŋ','n').replace('ǵ','gz')
        self.headword = Headword(self.lexicalunit)
        #self.collationform = normalizeword(self.citationform)
        self.collationkey = self.lexicalunit.lower()
        self.collationkey = self.collationkey.replace("ɡ",'g').replace('ɔ','ó').replace('ɛ','é').replace('ŋ','ń').replace('gb','ǵ')
        self.collationkey = self.collationkey+" "+self.order
        if self.collationkey[0] == '-':
          self.collationkey = self.collationkey[1:]
        try:
          self.note = self.element.find("note/form/text").text         #FIXME no semantics
        except AttributeError:
          pass
        self.pronunciation = fromformtext(self.element,'pronunciation')
        self.literalmeaning = fromfieldformtext(self.element,'literal-meaning')
        self.senses =  [Sense(s) for s in self.element.findall('sense')]
        #self.variants = self.get_variants()
        self.etymology_language, self.etymology_string = self.get_etymology()
        self.compares = self.get_compares()
        self.component_lexemes = self.get_component_lexemes()


    #def get_variants(self):
      #result = []
      #example_elements = self.element.findall('.//variant')
      #for ex in example_elements:
        #result.append(Example(ex))
      #return result


    def get_etymology(self):
      etymology_element = self.element.find("etymology")
      try:
        language = etymology_element.find("form").attrib['lang']
        string = etymology_element.find("form/text").text
      except AttributeError:
        return False, False
      return language, string

    def get_compares(self):
      relations = self.element.findall("relation")
      result = []
      for relation in relations:
          type_ = relation.attrib["type"]
          if type_ == "Compare":
            ref = relation.attrib["ref"]
            result.append(ref)
      return sorted(result)

    def get_component_lexemes(self):
      relations = self.element.findall("relation")
      if relations:
        result = []
        form_types = {}
        primary = ''
        for relation in relations:
            type_ = relation.attrib["type"]
            if type_ == "_component-lexeme":
              ID = relation.attrib["ref"]
              if ID == "":
                continue
              string = ID.split("_")[0].replace("-",'')
              for trait in relation.findall("trait"):
                if trait.attrib["name"]=="is-primary":
                  primary = (ID, string)
                if trait.attrib["name"]=="complex-form-type":
                  value = trait.attrib["value"].replace(" ", "")
                  form_types[value] = True
              result.append(numbers_to_subscript(string))
        form_type = "".join(sorted(form_types.keys()))
        fullstring = ", ".join(result)
        return form_type, fullstring, primary


    def toLatex(self):
        self.headword.toLatex()
        printsafe(self, 'citationform') #2 A
        printsafe(self, 'lexicalunit') #1 B
        printsafe(self, 'order') #2 A
        print(cmd("label",self.ID, escape_underscore=False))
        printsafe(self, 'pronunciation') #2 A
        if self.etymology_string:
          print(cmd('etymology', "%s}{%s" % (self.etymology_language,self.etymology_string)))
        #printsafe(self, 'plural')  #5 D
        for r in self.compares:
            target = r
            string = r.split("_")[0].replace(",",", ")
            string = numbers_to_subscript(string)
            print(cmd("compare",string+"}{"+target, escape_underscore=False))
        if self.component_lexemes and self.component_lexemes != ('','',''):
          form_type = self.component_lexemes[0]
          string = numbers_to_subscript(self.component_lexemes[1])
          try:
            principal_component_string = numbers_to_subscript(self.component_lexemes[2][1])
            principal_component_ID = self.component_lexemes[2][0]
          except IndexError:
            principal_component_ID = ''
            principal_component_string = ''
          print(cmd(form_type,string+"}{"+principal_component_ID+"}{"+principal_component_string, escape_underscore=False))
        if len(self.senses)==1:
            self.senses[0].toLatex()
        else:
            for i,s in enumerate(self.senses):
                s.toLatex(number=i+1)
        printsafe(self, 'literalmeaning') #4 J
        #printsafe(self, 'note') #3 J




class Headword():
    def __init__(self, s, firstwordofletter=False):
        #self.homograph = False
        self.firstwordofletter = firstwordofletter 
        self.word = s
        
    def toLatex(self):
        print("\\newentry")
        #print(cmd('headword',self.word))
        
class Pronunciation():
    def __init__(self,p): 
        self.ipa = p.find('.//Run').text 
        self.anchor = p.attrib.get('id',False)
        
    def toLatex(self): 
        latexipa = self.ipa.replace('ꜜ','{\downstep}')
        if self.anchor:
            print(hypercmd('ipa',self.anchor, latexipa, indent=1))
        else:
            print(cmd('ipa', latexipa, indent=1))

class Example():
  def __init__(self,el):
    self.reference = el.attrib.get("source", "\\nosource")
    self.vernacular = fromtext(el, "form/text") #NB: no label needed
    self.translation = fromformtext(el,"translation")


  def toLatex(self,number=False):
        if number:
          print("\\examplenumber{%s}%%"%number)
        try:
          print(f'{cmd("vernacular",self.vernacular)}')
          print(f'{cmd("translation",self.translation)}')
          #print(f'{cmd("reference",self.reference)}')
        except AttributeError:
          pass

    
class Sense():
    def get_examples(self, e):
      result = []
      example_elements = e.findall('.//example')
      for ex in example_elements:
        result.append(Example(ex))
      return result

    def __init__(self,s):
        self.element = s
        self.anchor = self.element.attrib.get('id',False)
        try:
          tmppos = self.element.find(".//grammatical-info").attrib["value"]
        except AttributeError:
          tmppos = "nopos"
        posd = {
          "Adjective":"adj",
          "Adverb":"adv",
          "Adposition":"adp",
          "Auxiliary verb":"aux",
          "Copula":"cop",
          "Coordinating connective":"coord. conn.",
          "Definite article":"def.art.",
          "Demonstrative":"dem",
          "Demonstrative pronoun":"dem.pron.",
          "Determiner":"det",
          "Discourse element":"Disco",
          "Ideophone":"ideo",
          "Indefinite pronoun":"indef",
          "Interjection":"interj",
          "Interrogative pro-form":"interr",
          "Locative":"loc",
          "Name":"Nam",
          "nopos":"\\nopos",
          "NCM":"ncm",
          "Noun":"n",
          "Noun class marker":"NCM",
          "Noun class pronoun":"ncp",
          "Number":"num",
          "Particle":"prt",
          "pers":"pers",
          "Personal pronoun":"pers.pron.",
          "Pronoun":"pron.",
          "Proper Noun":"prop.noun",
          "Postposition":"postp",
          "Preposition":"prep",
          "Pro-form":"pro",
          "pro-form":"pro",
          "pro":"pro",
          "Quantifier":"quant",
          "Subordinating connective":"subordconn.",
          "Temporal adverb":"temp.adv.",
          "Verb": "v",
          "v": "v"
        }
        try:
          self.pos = posd[tmppos.strip()]
        except KeyError:
          print(tmppos)
        self.glosses = fromtext(self.element,"gloss/text")
        self.definition = fromformtext(self.element,"definition")
        self.examples = self.get_examples(self.element)
        #self.scientificname = fromfieldformtext(self.element,'scientific-name')
        #self.sematicnote = fromnoteformtext(self.element,'semantics')



        
    
    def toLatex(self,number=False):
        if number:
          print(cmd('sensenr',number,indent=1))
        printsafe(self, 'pos') #8 C
        printsafe(self, 'scientificname') #9 D
        if self.__dict__.get('definition'):#7 E
            if self.anchor:
                print(hypercmd('definition',self.anchor,self.definition,indent=3))
            else:
              print(cmd('definition',self.definition,indent=3))
        else:
          printsafe(self, 'glosses') #6 0
        printsafe(self, 'semantics') #10 J
        if len(self.examples)==1:
          self.examples[0].toLatex()
        else:
          for i, example in enumerate(self.examples):
            example.toLatex(number=i+1)
            


  
  
  
            
#===================



fn = sys.argv[1]
tree = etree.parse(fn)
root = tree.getroot()

lexentries = []

for entry in root.findall('.//entry'):
  lexentries.append(LexEntry(entry))
  
linkd = {}
for le in lexentries:
  ID = le.ID
  headword = le.headword.word
  linkd[le.ID] = headword
   
startletter = 'a'
print("\\end{letter}\n\\begin{letter}{a}""")
for le in sorted(lexentries, key=lambda l: (l.normalizedfirstletter,l.firstletter,l.collationkey, l.lexicalunit)):
  print("%"+30*"-")
  if le.firstletter != startletter:
      print("\\end{letter}\n\\begin{letter}{%s}"""%(le.firstletter))
      startletter = le.firstletter
  le.toLatex()
print("\\end{letter}")
  
