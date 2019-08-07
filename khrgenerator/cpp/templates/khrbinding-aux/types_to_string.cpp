
#include <{{api.identifier}}binding-aux/types_to_string.h>

#include <ostream>
#include <bitset>
#include <sstream>

#include <{{api.identifier}}binding/Version.h>
#include <{{api}}binding-aux/Meta.h>

#include "types_to_string_private.h"


{{#types.items}}
{{#item.integrations.streamable}}
{{#item}}{{>partials/types_streamable.cpp}}{{/item}}

{{/item.integrations.streamable}}
{{#item.integrations.bitfieldStreamable}}
{{#item}}{{>partials/types_bitfieldStreamable.cpp}}{{/item}}

{{/item.integrations.bitfieldStreamable}}
{{/types.items}}


namespace {{api.identifier}}binding
{


template <>
std::ostream & operator<<(std::ostream & stream, const Value<{{api}}::{{enumType}}> & value)
{
    const auto name = aux::Meta::getString(value.value());
    stream.write(name.c_str(), static_cast<std::streamsize>(name.size()));

    return stream;
}

/*template <>
std::ostream & operator<<(std::ostream & stream, const Value<{{api}}::{{profile.bitfieldType}}> & value)
{
    std::stringstream ss;
    ss << "0x" << std::hex << static_cast<unsigned>(value.value());
    stream << ss.str();

    return stream;
}*/

template <>
std::ostream & operator<<(std::ostream & stream, const Value<{{api}}::{{profile.booleanType}}> & value)
{
    auto name = aux::Meta::getString(value.value());
    stream.write(name.c_str(), static_cast<std::streamsize>(name.size()));

    return stream;
}

{{#glapi}}
template <>
std::ostream & operator<<(std::ostream & stream, const Value<{{api}}::GLubyte *> & value)
{
    auto s = {{api}}binding::aux::wrapString(reinterpret_cast<const char*>(value.value()));
    stream.write(s.c_str(), static_cast<std::streamsize>(s.size()));

    return stream;
}

template <>
std::ostream & operator<<(std::ostream & stream, const Value<{{api}}::GLchar *> & value)
{
    auto s = {{api}}binding::aux::wrapString(reinterpret_cast<const char*>(value.value()));
    stream.write(s.c_str(), static_cast<std::streamsize>(s.size()));

    return stream;
}

template <>
std::ostream & operator<<(std::ostream & stream, const Value<{{api}}::GLuint_array_2> & value)
{
    std::stringstream ss;
    ss << "{ " << value.value()[0] << ", " << value.value()[1] << " }";
    stream << ss.str();

    return stream;
}
{{/glapi}}

std::ostream & operator<<(std::ostream & stream, const Version & version)
{
    stream << version.toString();

    return stream;
}

std::ostream & operator<<(std::ostream & stream, const AbstractValue * value)
{
    if (typeid(*value) == typeid(AbstractValue))
    {
        return stream << reinterpret_cast<const void*>(value);
    }

{{#glapi}}
    if (typeid(*value) == typeid(Value<{{api}}::GLvoid *>))
    {
        return stream << *reinterpret_cast<const Value<{{api}}::GLvoid *>*>(value);
    }
{{/glapi}}

{{#types.items}}
{{#item}}{{>partials/types_value_output.cpp}}{{/item}}
{{/types.items}}
    // expect an AbstractValue with a pointer in first member
    return stream << *reinterpret_cast<const Value<void *>*>(value);
}


} // namespace {{api.identifier}}binding