import adsk.core
import adsk.fusion
import adsk.cam
import traceback

## Global variable used to maintain a reference to all event handlers.
handlers = []
## global variable to maintain reference to the fusion ui
ui = None
## global variable to maintain reference to the fusion application
app = None
## global variable to keep track of how many via points are created
numberDarkRoomSensors = 0
## global variable to specify the links that can be choosen
links = []
## global variable to hold the root component of the model
rootComp = None

allDarkRoomSensors = []



## Event handler for the commandCreated event.
# 
# This event is called as soon as the button is created. It defines how the
# dialog window is displayed and what functions it has. 
class ButtonCommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        cmd = args.command

        # Connect to the command destroyed event.
        onDestroy = MyCommandDestroyHandler()
        cmd.destroy.add(onDestroy)
        handlers.append(onDestroy)

        # connect execute event handler
        onExecuteEvent = MyExecuteEventHandler()
        cmd.execute.add(onExecuteEvent)
        handlers.append(onExecuteEvent)

        # Connect to the input changed event.           
        onInputChanged = MyCommandInputChangedHandler()
        cmd.inputChanged.add(onInputChanged)
        handlers.append(onInputChanged)

        cmd.isOKButtonVisible = False
        inputs = cmd.commandInputs

        # Get all links the robot has
        global links
        links = getLinkNames()

        # Create tab 'add'
        tabCmdInput1 = inputs.addTabCommandInput('tab_1', 'Add DarkRoom Sensors');
        createTab1(tabCmdInput1)

def getLinkNames():
    # Get all links of the robot (all rigid groups)
    # get active design
    global app
    product = app.activeProduct
    design = adsk.fusion.Design.cast(product)
    # get root component in this design
    global rootComp
    rootComp = design.rootComponent
    # get all rigid groups of the root component
    links = []
    allRigidGroups = rootComp.allRigidGroups
    for rig in allRigidGroups:
        if rig is not None and rig.name[:6] == "EXPORT":
            links.append(rig.name[7:])
    return links

def createTab1(tabInput):
    childInputs = tabInput.children;

    # Create a message that spans the entire width of the dialog by leaving out the "name" argument.
    # TODO: Description
    message = '<div>Here is the description.</div>'
    childInputs.addTextBoxCommandInput('fullWidth_textBox', '', message, 1, True)

    # Create 'add' button
    # addButtonInput = childInputs.addBoolValueInput('tabAdd', 'Add', False, '', True)

    # # Create 'selection' button
    # selectionInput = childInputs.addSelectionInput('sel', 'Select', 'Select a circle for the via-point.')
    # selectionInput.setSelectionLimits(1,1)
    # selectionInput.addSelectionFilter("CircularEdges")

    addNewViaPoint(tabInput)

def addNewViaPoint(tabInput):
    # Get the CommandInputs object associated with the parent command.
    cmdInputs = adsk.core.CommandInputs.cast(tabInput.children)
    message = '<div>New DarkRoom Sensors</div>'
    cmdInputs.addTextBoxCommandInput('textBox{}'.format(numberDarkRoomSensors), '', message, 1, True)

    # add input for myomuscle number
    darkroomSensorIDInput = cmdInputs.addStringValueInput('darkroomSensorID{}'.format(numberDarkRoomSensors), 'DarkRoom Sensor ID [Int]')
    # add input for link name
    linkInput =  cmdInputs.addDropDownCommandInput('link{}'.format(numberDarkRoomSensors), 'Link Name', adsk.core.DropDownStyles.LabeledIconDropDownStyle);
    dropdownItems = linkInput.listItems
    # add a dropdown item for every link
    global links
    for lin in links:
        dropdownItems.add(lin, False, '')
    # Create a selection input.
    selectionInput = cmdInputs.addSelectionInput('selection{}'.format(numberDarkRoomSensors), 'Select', 'Select a vertex for the darkroom sensor location.')
    selectionInput.setSelectionLimits(1,1)

    # Increment number of ViaPoints
    global numberDarkRoomSensors
    numberDarkRoomSensors = numberDarkRoomSensors + 1

class MyDarkRoomSensor():
    number = ''
    link = ''
    vertex = None
        

# Event handler that reacts to any changes the user makes to any of the command inputs.
class MyCommandInputChangedHandler(adsk.core.InputChangedEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            eventArgs = adsk.core.InputChangedEventArgs.cast(args)
            inputs = eventArgs.inputs
            cmdInput = eventArgs.input

            if cmdInput.id == 'tabAdd':
                tabInput = cmdInput.parentCommandInput
                addNewViaPoint(tabInput)
            if cmdInput.id == 'selection0':
                selInput = inputs.itemById('selection0')
                selection  = selInput.selection(0)
                entity =  selection.entity

                numberInput = inputs.itemById('darkroomSensorID0')
                number = numberInput.value
                # get link name
                linkInput = inputs.itemById('link0').selectedItem
                link = '?'
                if linkInput:
                    link = linkInput.name

                global rootComp
                conPoints = rootComp.constructionPoints
                # Create construction point input
                pointInput = conPoints.createInput()
                # Create construction point by center
                pointInput.setByPoint(entity)
                point = conPoints.add(pointInput)
                point.name = "LS_" + link + "_" + number
                
                ls = MyDarkRoomSensor()
                ls.link = link
                ls.number = number
                ls.vertex = entity

                global allDarkRoomSensors
                allDarkRoomSensors.append(ls)

                # automatically increase VP number by 1
                numberInput.value = str(int(number) + 1)

        except:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))



## Event handler for the execute event.
# 
# This event is called when the 'OK' button in the dialog window is clicked.
# It then starts to create constuction points with a decent naming, so that
# the SDFusion exporter can then parse this information into an SDF file.
class MyExecuteEventHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        eventArgs = adsk.core.CommandEventArgs.cast(args)
        try:
            adsk.doEvents()          
        except:
            if ui:
                ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

# Event handler that reacts to when the command is destroyed. This terminates the script.            
class MyCommandDestroyHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            # When the command is done, terminate the script
            # This will release all globals which will remove all event handlers
            global allDarkRoomSensors
            for ls in allDarkRoomSensors:
                link = ls.link
                number = ls.number
                global rootComp
                conPoints = rootComp.constructionPoints
                # Create construction point input
                pointInput = conPoints.createInput()
                # Create construction point by center
                pointInput.setByPoint(ls.vertex)
                point = conPoints.add(pointInput)
                point.name = "LS_"+ link + "_" + number
                adsk.doEvents()
            adsk.terminate()
        except:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

## This function handles what happens as soon as the addin is started.
# 
# This function creates the button in Fusions UI. It connects the event
# that is called when the button is created.
def run(context):
    ui = None
    try:
        global app
        app = adsk.core.Application.get()
        global ui
        ui  = app.userInterface
        cmdDefs = ui.commandDefinitions

        # Create a button command definition.
        button = cmdDefs.itemById('DarkRoomSensorButtonID')
        if not button:
            button = cmdDefs.addButtonDefinition('DarkRoomSensorButtonID', 'DarkRoom-Sensors','DarkRoom-Sensors', './/Resources//DarkRoomSensors')

        # Connect to the command created event.
        ButtonCommandCreated = ButtonCommandCreatedHandler()
        button.commandCreated.add(ButtonCommandCreated)
        handlers.append(ButtonCommandCreated)

        # Create new panel
        ViaPointPanel = ui.workspaces.itemById('FusionSolidEnvironment').toolbarPanels.itemById('DarkRoomSensorPanelId')
        if not ViaPointPanel:
            ViaPointPanel = ui.workspaces.itemById('FusionSolidEnvironment').toolbarPanels.add('DarkRoomSensorPanelId', 'DARKROOM-SENSORS')
        buttonControl = ViaPointPanel.controls.addCommand(button, 'DarkRoomSensorButtonID')
        buttonControl.isPromoted = True

    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

## This function cleans up the document when the addin is stopped.
#
# To clean up the button in Fusions UI is removed.
def stop(context):
    global ui
    try:
        # Clean up the command.
        global ui
        addInsPanel = ui.allToolbarPanels.itemById('DarkRoomSensorPanelId')
        cntrl = addInsPanel.controls.itemById('DarkRoomSensorButtonID')
        if cntrl:
            cntrl.deleteMe()

    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
