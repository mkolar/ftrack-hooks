import sys
import argparse
import logging
import os
import getpass

import ftrack


class ComponentAdd(ftrack.Action):
    """Custom action."""

    #: Action identifier.
    identifier = "component.add"

    #: Action label.
    label = "ComponentAdd"

    def __init__(self):
        """Initialise action handler."""
        self.logger = logging.getLogger(
            __name__ + "." + self.__class__.__name__
        )

    def register(self):
        """Register action."""
        ftrack.EVENT_HUB.subscribe(
            "topic=ftrack.action.discover and source.user.username={0}".format(
                getpass.getuser()
            ),
            self.discover
        )

        ftrack.EVENT_HUB.subscribe(
            "topic=ftrack.action.launch and source.user.username={0} "
            "and data.actionIdentifier={1}".format(
                getpass.getuser(), self.identifier
            ),
            self.launch
        )

    def validateSelection(self, selection):
        """Return true if the selection is valid.

        """

        if selection:
            return False

        return False

    def discover(self, event):
        """Return action config if triggered on a single selection."""

        selection = event["data"].get("selection", [])

        if not selection:
            return

        entityType = selection[0]["entityType"]

        if entityType != "assetversion":
            return

        return {
            "items": [{
                "label": self.label,
                "actionIdentifier": self.identifier,
            }]
        }

    def launch(self, event):
        if "values" in event["data"]:
            # Do something with the values or return a new form.
            values = event["data"]["values"]

            data = event["data"]
            selection = data.get("selection", [])
            version = ftrack.AssetVersion(selection[0]["entityId"])

            if not values["component_name"] or not values["component_path"]:
                return {
                    "success": False,
                    "message": "Missing input."
                }

            if not os.path.exists(values["component_path"]):
                return {
                    "success": False,
                    "message": "Path doesn't exist."
                }

            try:
                version.createComponent(name=values["component_name"],
                                        path=values["component_path"])
                version.publish()
            except:
                return {
                    "success": False,
                    "message": "Component already exists."
                }

            return {
                "success": True,
                "message": "Component Added"
            }

        return {
            "items": [
                {
                    "label": "Component Name",
                    "type": "text",
                    "name": "component_name",
                },
                {
                    "label": "Component Path",
                    "type": "text",
                    "name": "component_path",
                }
            ]
        }


def register(registry, **kw):
    """Register action. Called when used as an event plugin."""
    # Validate that registry is the correct ftrack.Registry. If not,
    # assume that register is being called with another purpose or from a
    # new or incompatible API and return without doing anything.
    if registry is not ftrack.EVENT_HANDLERS:
        # Exit to avoid registering this plugin again.
        return

    logging.basicConfig(level=logging.INFO)
    action = ComponentAdd()
    action.register()


def main(arguments=None):
    """Set up logging and register action."""
    if arguments is None:
        arguments = []

    parser = argparse.ArgumentParser()
    # Allow setting of logging level from arguments.
    loggingLevels = {}
    for level in (
        logging.NOTSET, logging.DEBUG, logging.INFO, logging.WARNING,
        logging.ERROR, logging.CRITICAL
    ):
        loggingLevels[logging.getLevelName(level).lower()] = level

    parser.add_argument(
        "-v", "--verbosity",
        help="Set the logging output verbosity.",
        choices=loggingLevels.keys(),
        default="info"
    )
    namespace = parser.parse_args(arguments)

    """Register action and listen for events."""
    logging.basicConfig(level=loggingLevels[namespace.verbosity])

    ftrack.setup()
    action = ComponentAdd()
    action.register()

    ftrack.EVENT_HUB.wait()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
