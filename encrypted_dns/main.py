import encrypted_dns

__VERSION__ = '1.1.4'


def start():
    print("Starting Encrypted-DNS", __VERSION__)
    dns_config_object = encrypted_dns.Configuration()
    dns_controller = encrypted_dns.server.Controller(dns_config_object)
    dns_controller.start()
