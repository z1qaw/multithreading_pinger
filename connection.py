import requests
import time
import traceback
import threading
import os
import parsing

from queue import Queue
from datetime import datetime
from colorama import init, Fore, Style

'''
TODO:
- Create queue.Queue() child for create ierarchy
- Connect to database
- Make comments
'''


# colorama module initialization
init()

def log_str(_str, filename):
	"""Use for append string in file (specially for logging).

		Vars:
		_str: string
		filename: string. """
	with open(filename, 'a') as logfile:
		logfile.write('\n' + _str)
		logfile.close()

class CounterThread(threading.Thread):
	"""This thread counting and printing process status in format:
		225.02 min -- 23490/448219
			 ^                ^
	time elapsed (min) -- scanned IPs counter. """
	def __init__(self, queue, interval):
		''' Counter thread initializator.

		Vars:
		queue: queue.Queue() class, IPs queue;
		interval: int, interval used to counting and printing messages. '''
		super(CounterThread, self).__init__()
		self.setDaemon(True)

		self.queue = queue
		self.interval = interval
		self.start_time = time.time()
		self.start_qsize = queue.qsize()

	def counter(self, queue, interval, start_qsize):
		'''Counter method.

		Vars:
		queue: IPs queue;
		interval: int, interval used to counting
					 and printing messages.
		start_qsize: int, first queue size. '''
		time_elapsed = (time.time() - start_time) / 60
		# '%.2f'%... is flost digit cutter.
		# before: '2.8347247328', after: '2.83'
		output = '{0} min -- {1}/{2}'.format(
														'%.2f'%(time_elapsed), 
														str(start_qsize - queue.qsize()),
														str(start_qsize))
		print(output)

	def run(self):
		'''Counter thread runner. '''
		while True:
			self.counter(self.queue, self.interval, self.start_qsize)
			time.sleep(self.interval)


class ConnectorThread(threading.Thread):
	"""Thread used to trying connection to IP-address. """
	def __init__(self,
					 thread_name,
					 ip_queue,
					 ports_list,
					 start_ips_count,
					 https_proxy=None
					):
	"""ConnectorThread initializator.

		Vars:
		thread_name: string, this thread name;
		ip_queue: queue.Queue() class, IPs queue;
		ports_list: [1, 2, 3], list of ports which
						shold be scanned on gaves IP.
						file: ports.txt.
		start_ips_count: int, first IPs count.
		https_proxy: str. HTTPS Proxy for ConnectorThread
						 tryings. Example: 
							'https://10.10.1.11:1080' """
		super(ConnectorThread, self).__init__()
		self.setDaemon(True)

		self.session = requests.session()
		self.proxies = {'https': https_proxy}
		self.thread_name = thread_name
		self.ip_queue = ip_queue
		self.ports_list = ports_list
		self.start_ips_count = start_ips_count

	def pure_connect(self, address, timeout):
		'''Just trying GET connection.
			
			Vars:
			address: string, address to connection;
			timeout: int, connection timeout. '''
		resp = self.session.get(address,
										proxies=self.proxies,
										timeout=timeout
									  ).content
		return resp

	def try_conn(self,
					 ip,
					 ports_list,
					 start_ips_count,
					 timeout=5,
					 log=False,
					 good_log=True
					):
		for port in ports_list:
			this_url = 'http://' + ip + ':' + port
			html_filename = '{0}_{1}.html'.format(ip.replace('.', '-'),
															  port.replace('.', '-'))
			this_ips_count = self.start_ips_count - self.ip_queue.qsize()
			try:
				if log:
					output_log = \
					 '{0} -- {1} -- {2}/{3} -- TRY CONNECTING -- IP: {4} ...'.format(
									  str(datetime.now()),
									  str(self.thread_name),
									  str(this_ips_count),
									  str(self.ip_queue.qsize()),
									  this_url)
					print(output_log)
					log_str(output_log, 'all_log.txt')
				results = self.pure_connect(this_url, timeout)

				folder_name = 'html'
				if not os.path.exists(folder_name):
					os.makedirs(folder_name)
				with open(os.path.join(folder_name, html_filename), 'w', encoding='utf-8') as this_file:
					this_file.write(results.decode('utf-8'))
					this_file.close()
				if good_log or log:
					log_string = '{0} -- {1} -- {2}/{3} -- OK -- IP: {4} -- Filename: {5}'.format(
									  str(datetime.now()),
									  str(self.thread_name),
									  str(this_ips_count),
									  str(self.ip_queue.qsize()),
									  this_url,
									  html_filename)
					output_log = Fore.GREEN + log_string + Style.RESET_ALL
					log_str(log_string, 'all_log.txt')
					log_str(log_string, 'good_log.txt')

					print(output_log)
			except requests.exceptions.RequestException:
				if log:
					log_string = '{0} -- {1} -- {2}/{3} -- BAD -- IP: {4}.'.format(
									 str(datetime.now()),
									 str(self.thread_name),
									 str(this_ips_count),
									 str(self.start_ips_count),
									 this_url)
					output_log = Fore.RED + log_string + Style.RESET_ALL
					print(output_log)
					log_str(log_string, 'all_log.txt')

			except Exception as e:
				print(str(datetime.now) + ' Error:\n', traceback.format_exc())
				with open('errors_log.txt', 'a', encoding='utf-8') as errors_log:
					errors_log.write(str(datetime.now()) + ' ' + traceback.format_exc() + '\n\n')
					errors_log.close()
				print('Error was writed to errors_log.txt')


	def run(self):
		while True:
			self.try_conn(self.ip_queue.get(), self.ports_list, self.start_ips_count, self.start_ips_count)

def scan(ips, ports_list, threads_count=3):
	ip_queue = Queue()
	threads = []
	if len(ips) < 1:
		print(
			'''IP diapasones does not found. Please check ips.txt file.
			Diapasones should be in format:
			x.x.x.x:port-x.x.x.x:port
			x.x.x.x:port-x.x.x.x:port
			...''')
	else:
		for i in ips:
			for ip in ips[i]:
				ip_queue.put(ip)

		ip_queue_size = ip_queue.qsize()

		cnt = CounterThread(ip_queue, 20)
		cnt.start()

		for i in range(threads_count):
			threads.append(ConnectorThread('ConnectorThread' + str(i), ip_queue, ports_list, ip_queue_size))
			threads[i].start()
			# threads[i].join()

		ip_queue.join()

def main():
	ips = open('ips.txt', 'r')
	parsed_dict = parsing.parse_diapason(ips.read())
	ports = open('ports.txt', 'r')
	ports_list = parsing.parse_ports(ports.read())
	scan(parsing.diapason_info(parsed_dict), ports_list, 400)

if __name__ == '__main__':
	try:
		start_time = time.time()
		main()
		print("\n--- %s seconds ---" % (time.time() - start_time))
	except Exception as e:
		print('Error:\n', traceback.format_exc())

	input('Press ENTER to end')
