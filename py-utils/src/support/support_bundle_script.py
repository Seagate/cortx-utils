import asyncio

from cortx.utils.support.support_bundle import SupportBundle
from cortx.utils.cli_framework.command import Command
from cortx.utils.log import Log


class SupportBundleScript:
    @staticmethod
    def generate(comment: str, **kwargs):
        Log.init('support_bundle', '/var/log/cortx/utils/support', level='INFO',
            backup_count=5, file_size_in_mb=5)

        components = ''
        for key, value in kwargs.items():
            if key == 'components':
                components = value

        options = {'comment': comment,'components':components, 'comm': {'type': 'direct', \
            'target': 'csm.cli.support_bundle', 'method': 'generate_bundle', 'class': \
            'SupportBundle', 'is_static': True, 'params': {}, 'json': {}}, \
            'output': {}, 'need_confirmation': False, 'sub_command_name': \
            'generate_bundle'}

        cmd_obj = Command('generate_bundle', options, [])
        loop = asyncio.get_event_loop()
        res = loop.run_until_complete(SupportBundle.generate_bundle(cmd_obj))
        return res

    @staticmethod
    def get_bundle_status(bundle_id: str):
        # status
        import time
        time.sleep(5)

        options = {'bundle_id': bundle_id, 'comm': {'type': 'direct', \
            'target': 'csm.cli.support_bundle', 'method': 'get_bundle_status', 'class': \
            'SupportBundle', 'is_static': True, 'params': {}, 'json': {}}, \
            'output': {}, 'need_confirmation': False, 'sub_command_name': \
            'get_bundle_status'}

        cmd_obj = Command('get_bundle_status', options, [])
        loop = asyncio.get_event_loop()
        res = loop.run_until_complete(SupportBundle.get_bundle_status(cmd_obj))
        print('\n\nStatus - ', res, '\n')
        loop.close()


if __name__ == '__main__':
    # componets parameter is optional, if not specified support bundle
    # will be created for all components. You can specify multiple
    # components like components = ['utils', 'provisioner']
    bundle_obj = SupportBundleScript.generate(comment='Test support bundle generation')
    print(bundle_obj)
    bundle_id = str(bundle_obj).split('|')[1].strip()
    SupportBundleScript.get_bundle_status(bundle_id=bundle_id)
