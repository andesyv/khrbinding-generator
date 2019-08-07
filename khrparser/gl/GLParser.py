
import re

from khrparser.XMLParser import XMLParser

from khrapi.Version import Version
from khrapi.FeatureSet import FeatureSet
from khrapi.Extension import Extension

from khrapi.Import import Import
from khrapi.TypeAlias import TypeAlias
from khrapi.NativeType import NativeType

from khrapi.Enumerator import Enumerator
from khrapi.BitfieldGroup import BitfieldGroup
from khrapi.ValueGroup import ValueGroup
from khrapi.SpecialValues import SpecialValues
from khrapi.Constant import Constant
from khrapi.Function import Function
from khrapi.Parameter import Parameter

class GLParser(XMLParser):

    @classmethod
    def parseXML(cls, api, profile, registry):
        # Types
        for T in registry.iter("types"):
            for type in T.findall("type"):
                apiEntryTag = type.find("apientry")
                nameTag = type.find("name")
                text = type.text
                if apiEntryTag is not None and apiEntryTag.tail is not None:
                    if text is None:
                        text = apiEntryTag.tail.strip()
                    else:
                        text = text + apiEntryTag.tail.strip()

                if nameTag is not None and nameTag.tail is not None:
                    if text is None:
                        text = nameTag.tail.strip()
                    else:
                        text = text + nameTag.tail.strip()

                if type.tail is not None:
                    if text is None:
                        text = type.tail.strip()
                    else:
                        text = text + type.tail.strip()

                if text is None:
                    declaration = type.find("name").text

                    if declaration.startswith("struct"):
                        name = re.search('%s(.*)%s' % ("struct ", ""), declaration).group(1).strip()
                        api.types.append(NativeType(api, name, declaration))

                elif text.startswith("#include"):
                    importName = re.search('%s(.*)%s' % ("<", ">"), text).group(1).strip()
                    api.types.append(Import(api, type.attrib["name"], importName))

                elif text.startswith("#if"):
                    api.types.append(NativeType(api, type.attrib["name"], text))

                elif text.startswith("typedef"):
                    aliasName = re.search('%s(.*)%s' % ("typedef ", ";"), text).group(1).strip()
                    alias = api.typeByIdentifier(aliasName)
                    if alias is None:
                        alias = NativeType(api, aliasName, aliasName)

                    typename = nameTag.text
                    api.types.append(TypeAlias(api, typename, alias))

        # Constants
        for E in registry.iter("enums"):
            for enum in E.findall("enum"):
                constant = Constant(api, enum.attrib["name"], enum.attrib["value"])
                if "group" in E.attrib and E.attrib["group"] == "SpecialNumbers":
                    constant.type = cls.detectSpecialValueType(api, enum)
                api.constants.append(constant)

        # Groups

        for G in registry.iter("groups"):
            for group in G.findall("group"):
                name = group.attrib["name"]

                if name.find("Mask") >= 0 or name == "PathFontStyle":
                    type = BitfieldGroup(api, name)
                elif name.find("Boolean") >= 0:
                    type = ValueGroup(api, name)
                else:
                    type = Enumerator(api, name)
                
                for enum in group.findall("enum"):
                    constant = api.constantByIdentifier(enum.attrib["name"])
                    if constant is None:
                        continue
                    type.values.append(constant)
                    constant.groups.append(type)
                
                if len(type.values) > 0:
                    api.types.append(type)
        
        for E in registry.iter("enums"):
            if "group" in E.attrib:
                name = E.attrib["group"]

                type = api.typeByIdentifier(name)

                if type is None and (name.find("Mask") >= 0 or name == "PathFontStyle"):
                    type = BitfieldGroup(api, name)
                    api.types.append(type)
                elif type is None and name.find("Boolean") >= 0:
                    type = ValueGroup(api, name)
                    api.types.append(type)
                elif type is None:
                    type = Enumerator(api, name)
                    api.types.append(type)

                for enum in E.findall("enum"):
                    constant = api.constantByIdentifier(enum.attrib["name"])
                    if constant is None or constant in type.values:
                        continue
                    type.values.append(constant)
                    constant.groups.append(type)

        # Functions
        for C in registry.iter("commands"):
            for command in C.iter("command"):
                protoTag = command.find("proto")
                returnTypeTag = protoTag.find("ptype")
                if returnTypeTag:
                    print(returnTypeTag.text)
                returnTypeName = returnTypeTag.text.strip() if returnTypeTag is not None else protoTag.text.strip()
                name = protoTag.find("name").text.strip()

                function = Function(api, name)
                returnType = api.typeByIdentifier(returnTypeName)
                if returnType is None:
                    returnType = NativeType(api, returnTypeName, returnTypeName)
                    api.types.append(returnType)
                function.returnType = returnType

                for param in command.findall("param"):
                    groupName = None # param.attrib.get("group", None) # Ignore group names for now
                    typeTag = param.find("ptype")
                    if groupName is not None:
                        typeName = groupName
                    else:
                        typeName = param.text if param.text else ""
                        if typeTag is not None:
                            if typeTag.text:
                                typeName += typeTag.text
                            if typeTag.tail:
                                typeName += typeTag.tail
                        typeName = typeName.strip()
                    name = param.find("name").text
                    type = api.typeByIdentifier(typeName)
                    if type is None:
                        type = NativeType(api, typeName, typeName)
                        api.types.append(type)

                    function.parameters.append(Parameter(function, name, type))

                api.functions.append(function)

        # Extensions
        for E in registry.iter("extensions"):
            for xmlExtension in E.findall("extension"):
                extension = Extension(api, xmlExtension.attrib["name"])

                for require in xmlExtension.findall("require"):
                    for child in require:
                        if child.tag == "enum":
                            extension.requiredConstants.append(api.constantByIdentifier(child.attrib["name"]))
                        elif child.tag == "command":
                            function = api.functionByIdentifier(child.attrib["name"])
                            extension.requiredFunctions.append(function)
                            function.requiringFeatureSets.append(extension)
                        elif child.tag == "type":
                            extension.requiredTypes.append(api.typeByIdentifier(child.attrib["name"]))

                api.extensions.append(extension)

        # Versions
        for feature in registry.iter("feature"):

            version = Version(api, feature.attrib["api"], feature.attrib["number"])

            for require in feature.findall("require"):
                comment = require.attrib.get("comment", "")
                if comment.startswith("Reuse tokens from "):
                    requiredExtension = re.search('%s([A-Za-z0-9_]+)' % ("Reuse tokens from "), comment).group(1).strip()
                    version.requiredExtensions.append(api.extensionByIdentifier(requiredExtension))
                elif comment.startswith("Reuse commands from "):
                    requiredExtension = re.search('%s([A-Za-z0-9_]+)' % ("Reuse commands from "), comment).group(1).strip()
                    version.requiredExtensions.append(api.extensionByIdentifier(requiredExtension))
                elif comment.startswith("Reuse "):
                    requiredExtension = re.search('%s([A-Za-z0-9_]+)' % ("Reuse "), comment).group(1).strip()
                    version.requiredExtensions.append(api.extensionByIdentifier(requiredExtension))
                elif comment.startswith("Promoted from "):
                    requiredExtension = re.search('%s([A-Za-z0-9_]+)' % ("Promoted from "), comment).group(1).strip()
                    version.requiredExtensions.append(api.extensionByIdentifier(requiredExtension))

                if comment.startswith("Not used by the API"):
                    continue

                for child in require:
                    if child.tag == "enum":
                        version.requiredConstants.append(api.constantByIdentifier(child.attrib["name"]))
                    elif child.tag == "command":
                        function = api.functionByIdentifier(child.attrib["name"])
                        version.requiredFunctions.append(function)
                        function.requiringFeatureSets.append(version)
                    elif child.tag == "type":
                        version.requiredTypes.append(api.typeByIdentifier(child.attrib["name"]))

            for remove in feature.findall("remove"):
                for child in remove:
                    if child.tag == "enum":
                        version.removedConstants.append(api.constantByIdentifier(child.attrib["name"]))
                    elif child.tag == "command":
                        version.removedFunctions.append(api.functionByIdentifier(child.attrib["name"]))
                    elif child.tag == "type":
                        version.removedTypes.append(api.typeByIdentifier(child.attrib["name"]))

            api.versions.append(version)

        return api

    @classmethod
    def patch(cls, profile, api):

        # Generic None Bit
        genericNoneBit = Constant(api, profile.noneBitfieldValue, "0x0")
        genericNoneBit.generic = True
        api.constants.append(genericNoneBit)
        for group in [ group for group in api.types if isinstance(group, BitfieldGroup) ]:
            group.values.append(genericNoneBit)
            genericNoneBit.groups.append(group)
        
        # Remove shared enum and bitfield GL_NONE
        noneBit = api.constantByIdentifier("GL_NONE")
        if noneBit is not None:
            for group in noneBit.groups:
                if isinstance(group, BitfieldGroup):
                    group.values.remove(noneBit)
            if len(noneBit.groups) == 0:
                api.constants.remove(noneBit)

        # Fix Special Values
        specialNumbersType = None
        for constant in api.constants:
            if len(constant.groups) == 1 and constant.groups[0].identifier == "SpecialNumbers" and constant.type is not None:
                if specialNumbersType is None:
                    specialNumbersType = SpecialValues(api, "SpecialValues")
                    api.types.append(specialNumbersType)
            
                specialNumbersType.values.append(constant)
                constant.groups = [specialNumbersType]

        # Assign Ungrouped
        ungroupedType = None
        for constant in api.constants:
            if len(constant.groups) == 0 and constant.type is None:
                if ungroupedType is None:
                    ungroupedType = Enumerator(api, "UNGROUPED")
                    api.types.append(ungroupedType)
            
                ungroupedType.values.append(constant)
                constant.groups.append(ungroupedType)
        
        # Add generic Feature Sets
        allFeatureSet = FeatureSet(api, "gl")
        allFeatureSet.requiredExtensions = api.extensions
        allFeatureSet.requiredFunctions = api.functions
        allFeatureSet.requiredConstants = api.constants
        allFeatureSet.requiredTypes = api.types
        api.versions.append(allFeatureSet)
        
        return api

    @classmethod
    def detectSpecialValueType(cls, api, enum):
        if "comment" in enum.attrib:
            if re.search('Not an API enum.*', enum.attrib["comment"]) is not None:
                return None

            result = re.search('%s([A-Za-z0-9_]+)' % ("Tagged as "), enum.attrib["comment"])
            if result is not None:
                typeName = result.group(1).strip()
                return next((t for t in api.types if t.identifier.endswith(typeName)), api.typeByIdentifier("GLuint"))
        
        return api.typeByIdentifier("GLuint")
