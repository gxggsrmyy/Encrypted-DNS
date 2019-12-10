import os
import random
import socket
import threading
import time

from encrypted_dns import upstream, parse, utils, log, server


class Controller:
    def __init__(self, dns_config_object):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server.bind(('', 0))
        (self.controller_address, self.controller_port) = ('localhost', self.server.getsockname()[1])
        self.dns_config = dns_config_object.get_config()
        self.dns_map = {}
        self.listen_thread_list = []

        self.cache = {}
        self.enable_cache = self.dns_config['enable_cache']
        self.hosts = self.load_hosts()
        self.dns_bypass_china = self.dns_config['dns_bypass_china']

        upstream_timeout = self.dns_config['upstream_timeout']
        self.bootstrap_dns_object = upstream.UDPUpstream(self, self.controller_port,
                                                         self.dns_config['bootstrap_dns_address'], upstream_timeout)

        self.enable_log = self.dns_config['enable_log']
        if self.enable_log:
            self.logger = log.Logger()
            self.logger.create_log()

        self.init_listen()

    def load_hosts(self):
        hosts = self.dns_config['hosts']

        current_dir = os.path.dirname(os.path.abspath(__file__)).rstrip('/').rstrip('server')
        if self.dns_config['force_safe_search']:
            hosts.update(utils.load_hosts_from_file(current_dir + 'filter_lists/safe_search.txt'))
        if self.dns_config['block_ads']:
            hosts.update(utils.load_hosts_from_file(current_dir + 'filter_lists/ads.txt'))

        for name in hosts:
            if utils.is_valid_ipv4_address(hosts[name]):
                hosts[name] = [hosts[name], 'A']
            else:
                hosts[name] = [hosts[name], 'CNAME']
        return hosts

    def init_listen(self):
        try:
            listen_config = self.dns_config['listen']
            for listen in listen_config:
                listen['client_blacklist'] = self.dns_config['client_blacklist']
                if listen['protocol'] == 'udp':
                    listen_object = server.UDPServer(listen, (self.controller_address, self.controller_port))
                    self.listen_thread_list.append(
                        threading.Thread(target=listen_object.start, args=(), daemon=True).start())

        except OSError as exc:
            print(str(exc))
            exit()

    def start(self):
        try:
            while True:
                recv_data, recv_address = self.server.recvfrom(512)
                recv_header = parse.ParseHeader.parse_header(recv_data)
                if self.enable_log:
                    self.logger.write_log('recv_data:' + str(recv_data))

                transaction_id = recv_header['transaction_id']
                if self.enable_log:
                    self.logger.write_log('transaction_id:' + str(transaction_id))

                if recv_header['flags']['QR'] == '0':
                    self.dns_map[transaction_id] = [recv_address, 0]
                    query_thread = threading.Thread(target=self.handle_query, args=(transaction_id, recv_data,))
                    query_thread.daemon = True
                    query_thread.start()

                elif recv_header['flags']['QR'] == '1' and transaction_id in self.dns_map:
                    response = self.handle_response(recv_data)
                    sendback_address = self.dns_map[transaction_id][0]

                    if self.dns_bypass_china and response[2]:
                        if len(response[2]) > 1:
                            ip_address = response[2][-1]['record']
                        else:
                            ip_address = response[2][0]['record']

                        current_dir = os.path.dirname(os.path.abspath(__file__)).rstrip('/').rstrip('server')
                        if self.dns_map[transaction_id][1] == 1 or (
                                utils.is_valid_ipv4_address(ip_address) and utils.is_subnet_address(
                                current_dir + 'filter_lists/chnroute.txt', ip_address)
                        ):
                            self.server.sendto(recv_data, sendback_address)
                            self.dns_map.pop(transaction_id)
                        elif self.dns_map[transaction_id][1] == 0:
                            self.dns_map[transaction_id][1] = 1
                            continue
                    else:
                        self.server.sendto(recv_data, sendback_address)
                        self.dns_map.pop(transaction_id)

                    if self.enable_cache and response[2]:
                        response_name = utils.get_domain_name_string(response[1]['QNAME'])
                        if response_name != '':
                            response_type = response[1]['QTYPE']
                            response_ttl = response[2][0]['ttl']
                            if response_name not in self.cache:
                                self.cache[response_name] = {}
                            self.cache[response_name][response_type] = [recv_data, int(time.time()), response_ttl]

        except socket.timeout as exc:
            print('[Error]', str(exc))
            self.start()

        except KeyboardInterrupt:
            print('Stop Encrypted-DNS Resolver')
            exit()

        except Exception as exc:
            print('[Error]', str(exc))
            self.start()

    def _send(self, response_data, address):
        self.server.sendto(response_data, address)

    def handle_query(self, transaction_id, query_data):
        try:
            query_parser = parse.ParseQuery(query_data)
            parse_result = query_parser.parse_plain()
            query_name_list = parse_result[1]['QNAME']
            query_type = parse_result[1]['QTYPE']
            query_name = utils.get_domain_name_string(query_name_list)

            if self.enable_log:
                self.logger.write_log('query_parse_result:' + str(parse_result))

            cache_query = None
            cached = False

            for item in self.hosts.keys():
                if query_name == item or (item.startswith("include:") and item.lstrip("include:") in query_name):
                    response_data = utils.struct_response(query_name, str(transaction_id),
                                                          query_type, self.hosts[item][0],
                                                          self.hosts[item][1])
                    sendback_address = self.dns_map[transaction_id][0]
                    self.server.sendto(response_data, sendback_address)
                    self.dns_map.pop(transaction_id)
                    return

            if self.enable_cache and query_name in self.cache and query_type in self.cache[query_name]:
                cache_query = self.cache[query_name][query_type]
                cache_time = cache_query[1]
                cache_ttl = cache_query[2]
                current_time = int(time.time())

                if current_time - cache_time > cache_ttl:
                    self.cache[query_name].pop(query_type)
                else:
                    cached = True

            if cached:
                cache_query_result = cache_query[0]
                cache_query_result = bytes.fromhex(transaction_id) + cache_query_result[2:]
                sendback_address = self.dns_map[transaction_id][0]
                self.server.sendto(cache_query_result, sendback_address)
                self.dns_map.pop(transaction_id)
            else:
                if query_name in self.dns_config['dns_bypass']:
                    upstream_object = self.bootstrap_dns_object
                    upstream_object.query(query_data)
                elif self.dns_bypass_china:
                    upstream_object = self.bootstrap_dns_object
                    upstream_object.query(query_data)
                    upstream_object = self.select_upstream()
                    upstream_object.query(query_data)
                else:
                    upstream_object = self.select_upstream()
                    upstream_object.query(query_data)

        except IndexError as exc:
            print('[Error]', str(exc))

        except KeyboardInterrupt:
            print('Stop Encrypted-DNS Resolver')
            exit()

        except Exception as exc:
            print('[Error]', str(exc))
            raise exc

    def select_upstream(self):
        upstream_dns_list = self.dns_config['upstream_dns']
        enable_weight = self.dns_config['upstream_weight']
        upstream_timeout = self.dns_config['upstream_timeout']
        weight_list = []

        if enable_weight:
            for item in upstream_dns_list:
                weight_list.append(item['weight'])
            upstream_dns = random.choices(population=upstream_dns_list, weights=weight_list, k=1)
            upstream_dns = upstream_dns[0]
        else:
            upstream_dns = random.choice(upstream_dns_list)

        protocol = upstream_dns['protocol']
        port = self.controller_port

        if protocol == 'udp':
            upstream_object = upstream.UDPUpstream(self, port, upstream_dns, upstream_timeout)
        elif protocol == 'tcp':
            upstream_object = upstream.TCPUpstream(self, port, upstream_dns, upstream_timeout)
        elif protocol == 'https':
            upstream_object = upstream.HTTPSUpstream(self, port, upstream_dns, upstream_timeout)
        elif protocol == 'tls':
            upstream_object = upstream.TLSUpstream(self, port, upstream_dns, upstream_timeout)
        else:
            return None
        return upstream_object

    def handle_response(self, response_data):
        response_parser = parse.ParseResponse(response_data)
        parse_result = response_parser.parse_plain()
        if self.enable_log:
            self.logger.write_log('response_parse_result:' + str(parse_result))
        return parse_result
