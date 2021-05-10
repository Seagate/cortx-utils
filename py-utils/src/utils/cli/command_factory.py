import argparse
import sys
import os
from cortx.utils.schema.payload import Json
from cortx.utils.cli import const
from cortx.utils.log import Log
from csm.cli.command import CommandParser


class ArgumentParser(argparse.ArgumentParser):
    """Overwritten ArgumentParser class for internal purposes"""

    def error(self, message):
        # todo:  Need to Modify the changes for Fetching Error Messages from config file
        self.print_usage(sys.stderr)
        self.exit(2, f'Error: {message.capitalize()}\n')


class CommandFactory(object):
    """
    Factory for representing and creating command objects using
    a generic skeleton.
    """

    @staticmethod
    def get_command(argv, permissions={}, component_cmd_dir="", excluded_cmds=[], hidden_cmds=[]):
        """
        Parse the command line as per the syntax and retuns
        returns command representing the command line.
        """
        #TODO: Validate component_cmd_dir exists else raise error
        if len(argv) <= 1:
            argv.append("-h")
        default_commands = os.listdir(const.COMMAND_DIRECTORY)
        commands_files = os.listdir(component_cmd_dir)
        commands_files.extend(default_commands)
        excluded_cmds.extend(const.EXCLUDED_COMMANDS)

        commands = [command.split(".json")[0] for command in commands_files
                    if command.split(".json")[0] not in excluded_cmds]
        if permissions:
            # common commands both in commands and permissions key list
            commands = [command for command in commands if command in permissions.keys()]
        parser = ArgumentParser(description='Cortx cli commands')
        hidden_cmds.extend(const.HIDDEN_COMMANDS)
        metavar = set(commands).difference(set(hidden_cmds))
        subparsers = parser.add_subparsers(metavar=metavar)
        filter_cmd_dir_obj = filter(lambda dir: f"{argv[0]}.json" in os.listdir(dir) ,
                                        [component_cmd_dir, const.COMMAND_DIRECTORY])
        filter_cmd_dir=list(filter_cmd_dir_obj)
        if filter_cmd_dir:
            # get command json file and filter only allowed first level sub_command
            # create filter_permission_json
            cmd_from_file = Json(os.path.join(filter_cmd_dir[0], f"{argv[0]}.json")).load()
            cmd_obj = CommandParser(cmd_from_file, permissions.get(argv[0], {}))
            cmd_obj.handle_main_parse(subparsers)
        namespace = parser.parse_args(argv)

        CommandFactory.edit_arguments(namespace)

        sys_module = sys.modules[__name__]
        for attr in ['command', 'action', 'args']:
            setattr(sys_module, attr, getattr(namespace, attr))
            delattr(namespace, attr)
        return command(action, vars(namespace), args)

    @staticmethod
    def edit_arguments(namespace):
        # temporary solution till user create api is not fixed
        # remove when fixed
        if namespace.action == 'users' and namespace.sub_command_name == 'create':
            namespace.roles = [namespace.roles]
