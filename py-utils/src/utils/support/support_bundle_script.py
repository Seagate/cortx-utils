import asyncio
import getpass
import errno

from cortx.utils.support.bundle_generate import ComponentsBundle
from cortx.utils.support.support_bundle import SupportBundle
from cortx.utils.cli_framework.command import Command
from cortx.utils.schema.providers import Response


class SupportBundleScript:
    @staticmethod
    def generate(node_name: str, comment: str, components: list):
        current_user = str(getpass.getuser())
        # Check if User is Root User.
        if current_user.lower() != 'root':
            response_msg = "Support Bundle Command requires root privileges"
            return Response(output=response_msg, rc=errno.EACCES)

        bundle_id = SupportBundle._generate_bundle_id()

        options = {'bundle_id': bundle_id, 'comment': comment, 'node_name': \
            node_name, 'components': components, 'comm': {'type': 'direct', \
            'target': 'csm.cli.support_bundle', 'method': 'init', 'class': \
            'ComponentsBundle', 'is_static': True, 'params': {}, 'json': {}}, \
            'output': {}, 'need_confirmation': False, 'sub_command_name': \
            'bundle_generate'}

        cmd_obj = Command('bundle_generate', options, [])
        loop = asyncio.get_event_loop()
        loop.run_until_complete(ComponentsBundle.init(cmd_obj))
        return bundle_id

    @staticmethod
    def get_bundle_status(bundle_id: str):
        # status
        import time
        time.sleep(3)

        options = {'bundle_id': bundle_id, 'comm': {'type': 'direct', \
            'target': 'csm.cli.support_bundle', 'method': 'init', 'class': \
            'SupportBundle', 'is_static': True, 'params': {}, 'json': {}}, \
            'output': {}, 'need_confirmation': False, 'sub_command_name': \
            'get_bundle_status'}

        cmd_obj = Command('get_bundle_status', options, [])
        loop = asyncio.get_event_loop()
        res = loop.run_until_complete(SupportBundle.get_bundle_status(cmd_obj))
        print('\n\nStatus - ', res, '\n')
        loop.close()


if __name__ == '__main__':
    bundle_id = SupportBundleScript.generate(
        comment='Test support bundle generation', node_name='srvnode-1',
        components=['utils'])
    SupportBundleScript.get_bundle_status(bundle_id=bundle_id)
