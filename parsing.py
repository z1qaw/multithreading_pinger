import re

def parse_ports(pure_text):
   ports_list = re.findall('\d+', pure_text)
   return ports_list

def diapason_info(diapasones_dict, log=False):

   if not diapasones_dict:
      return 0
   needed_ips = {}
   i = 0
   total = 0
   for diapason in diapasones_dict:
      needed_ips[i] = []
      this_total = 0
      diapason_from = diapasones_dict[diapason]['from']
      diapason_to = diapasones_dict[diapason]['to']
      for a in range(diapason_from['0'], diapason_to['0'] + 1):
         for b in range(diapason_from['1'], diapason_to['1'] + 1):
            for c in range(diapason_from['2'], diapason_to['2'] + 1):
               for d in range(diapason_from['3'], diapason_to['3'] + 1):
                  needed_ips[i].append('.'.join([str(a), str(b), str(c), str(d)]))
                  total += 1
                  this_total += 1
      if log: print('Diapason {0} total: {1}'.format(str(i), str(this_total)))

      i += 1
   print('-'*10)
   print('Total: ' + str(total))
   
   return needed_ips

def parse_diapason(pure_text):
   pattern = r'\d+\.\d+\.\d+\.\d+\-\d+\.\d+\.\d+\.\d+'
   text = re.findall(pattern, pure_text.replace(' ', ''))
   parsed_dict = {}

   i = 0
   for string in text:
      if string.replace(' ', ''):
         from_ip, to_ip = string.split('-')
      else:
         continue

      parsed_dict[i] = {}
      parsed_dict[i]['from'] = {}
      parsed_dict[i]['to'] = {}

      counts = from_ip.split('.')
      i_ = 0
      for var in counts:
         parsed_dict[i]['from'][str(i_)] = int(var)
         i_ += 1

      counts = to_ip.split('.')
      i_ = 0
      for var in counts:
         parsed_dict[i]['to'][str(i_)] = int(var)
         i_ += 1

      i += 1

   return parsed_dict
