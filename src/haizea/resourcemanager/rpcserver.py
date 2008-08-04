# -------------------------------------------------------------------------- #
# Copyright 2006-2008, University of Chicago                                 #
# Copyright 2008, Distributed Systems Architecture Group, Universidad        #
# Complutense de Madrid (dsa-research.org)                                   #
#                                                                            #
# Licensed under the Apache License, Version 2.0 (the "License"); you may    #
# not use this file except in compliance with the License. You may obtain    #
# a copy of the License at                                                   #
#                                                                            #
# http://www.apache.org/licenses/LICENSE-2.0                                 #
#                                                                            #
# Unless required by applicable law or agreed to in writing, software        #
# distributed under the License is distributed on an "AS IS" BASIS,          #
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.   #
# See the License for the specific language governing permissions and        #
# limitations under the License.                                             #
# -------------------------------------------------------------------------- #

import threading
from SimpleXMLRPCServer import SimpleXMLRPCServer

DEFAULT_HAIZEA_PORT = 42493

class RPCServer(object):
    def __init__(self, rm):
        self.rm = rm
        self.logger = self.rm.logger
        self.port = DEFAULT_HAIZEA_PORT
        self.server = SimpleXMLRPCServer(("localhost", self.port))
        self.register_rpc(self.test_func)
        self.register_rpc(self.cancel_lease)
        self.register_rpc(self.get_leases)
        self.register_rpc(self.get_lease_info)
        self.register_rpc(self.get_queue)
        self.register_rpc(self.notify_event)

    def start(self):
        # Start the XML-RPC server
        server_thread = threading.Thread( target = self.serve )
        server_thread.start()
        
    def register_rpc(self, func):
        self.server.register_function(func)
        
    def serve(self):
        self.logger.info("RPC server started on port %i" % self.port, "RPC")
        self.server.serve_forever()        
        
    def test_func(self):
        self.logger.info("Test RPC function called", "RPC")
        return 0
    
    def cancel_lease(self, lease_id):
        pass

    def get_leases(self):
        pass

    def get_lease_info(self):
        pass

    def get_queue(self):
        pass

    def notify_event(self, lease_id, enactment_id, event):
        pass