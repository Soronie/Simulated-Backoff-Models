import random	
import simpy
import math

Ts = 1
total_hosts = 10
initial_slot_num = 0
SIM_TIME = 100000


class Packet:
    def __init__(self, identifier, arrival_time):
        self.identifier = identifier
        self.arrival_time = arrival_time

# Server class that has hosts transmitting in parallel and
# checks for collisions

class Server:
    def __init__(self, env, arrival_rate, hosts, slot_number):
        self.server = simpy.Resource(env, capacity=1)
        self.env = env
        self.hosts = hosts
        self.packet_number = 0
        self.successes = 0
        self.failures = 0
        self.slot_number = slot_number
        self.arrival_rate = arrival_rate

    def CollisionTracker(self, env, alg):
        while True:
            active_hosts = []
            for host in self.hosts:
                # If there are 1 or more packets in queue and host slot number
                # matches the next calculated one, it is active
                if host.l != 0 and host.s == self.slot_number:
                    active_hosts.append(host)

            # Success, so bring a new packet to the head of the queue
            if len(active_hosts) == 1:
                self.successes += 1
                for host in active_hosts:
                    host.Success()
                    self.packet_number += 1
                    arrival_time = env.now
                    new_packet = Packet(self.packet_number,arrival_time)
            # Failure, either exponential or linear if more than one host is actively transmitting
            else:
                for host in active_hosts:
                    host.setN(host.N()+1)
                    if alg == 0:
                        # Use exponential back-off algorithm
                        host.setS(host.S() + Ts + min(random.randrange(2**10),random.randrange(2**host.N())))
                        self.failures += 1
                    else:
                        # Use linear back-off algorithm
                        host.setS(host.S() + Ts + min(random.randrange(1024),random.randrange(host.N())))
                        self.failures += 1

            # Increaee potential slot number for next packet transmission
            # Ensure that packets transmit using slotted ALOHA
            self.slot_number += 1
            yield env.timeout(Ts)

    def packets_arrival(self, env, h):
        while True:
            # Produce random delays among packet transmissions as part of slotted ALOHA
            yield env.timeout(random.expovariate(self.arrival_rate))
            h.l += 1
            # If only one host is active, increase slot number for next transmission
            if h.l == 1:
                h.s = self.slot_number + 1

# L = number of packets in the queue.
# N = number of packets that were retransmitted
# S = slot number when a packet at the head of the queue transmits
class Host:
    def __init__(self, packets, slot_number, retransmits):
        self.l = packets
        self.n = retransmits
        self.s = slot_number

    def L(self):
        return self.l

    def N(self):
        return self.n

    def S(self):
        return self.s

    def setN(self, newValue):
        self.n = newValue

    def setS(self, newValue):
        self.s = newValue

# On success:
    # Decrement number of packets in queue (L)
    # Reset number of retransmissions (N)
    # Increment slot number (S)
    def Success(self):
        self.l -= 1
        self.n = 0
        self.s += 1
        return

def Throughput(successes, total):
    # Prevent divide-by-zero exception
    if total == 0:
        return 0
    return float(successes) / float(total)


def main():
    for arrival_rate in [0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09]:
        exp = 0
        lin = 0
        total_transmissions = 0
        algorithm = 0
        typeofalg = ""

        while(algorithm < 2):
            env = simpy.Environment()
            hosts = []

            # Initialize host objects and put them in a list
            for i in range(0, total_hosts):
                hosts.append(Host(0,0,0))

            server = Server(env, arrival_rate, hosts, initial_slot_num)
            # Produce initial processes for each host
            for i in range(0, total_hosts):
                env.process(server.packets_arrival(env,server.hosts[i]))

            # Check collisions among hosts
            env.process(server.CollisionTracker(env, algorithm))
            env.run(until=SIM_TIME)
            total_transmissions = server.successes + server.failures

            # The first iteration is for exponential; second is for linear
            if algorithm == 0:
                exp = Throughput(server.successes, total_transmissions)
            else:
                lin = Throughput(server.successes, total_transmissions)

            # For output purposes
            if algorithm == 0:
                typeofalg = "Exp"
            else:
                typeofalg = "Lin"

            print(typeofalg + " successes: {0:<7} Total: {1:<7}".format(server.successes, total_transmissions))

            # Increment to now do the same thing for linear backoff
            algorithm += 1

        print("{0:<10} {1:<20} {2:<20}".format("Lambda", "Exponential", "Linear"))
        print("{0:<10} {1:<20} {2:<20}\n".format(arrival_rate,
            round(exp,5), round(lin,5)))


if __name__ == '__main__': main()
