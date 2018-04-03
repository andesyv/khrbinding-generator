
#pragma once


#include <set>
#include <vector>
#include <functional>

#include <{{binding}}/{{binding}}_api.h>
#include <{{binding}}/{{binding}}_features.h>

#include <{{binding}}/CallbackMask.h>
#include <{{binding}}/ProcAddress.h>


namespace {{binding}}
{


class AbstractFunction;
class FunctionCall;


using SimpleFunctionCallback = std::function<void(const AbstractFunction &)>;
using FunctionCallback = std::function<void(const FunctionCall &)>;
using FunctionLogCallback = std::function<void(FunctionCall *)>;

{{ucbinding}}_API void initialize({{binding}}::GetProcAddress functionPointerResolver, bool resolveFunctions = true);
{{ucbinding}}_API void registerAdditionalFunction(AbstractFunction * function);
{{ucbinding}}_API ProcAddress resolveFunction(const char * name);
{{ucbinding}}_API void resolveFunctions();

{{ucbinding}}_API void setCallbackMask(CallbackMask mask);
{{ucbinding}}_API void setCallbackMaskExcept(CallbackMask mask, const std::set<std::string> & blackList);
{{ucbinding}}_API void addCallbackMask(CallbackMask mask);
{{ucbinding}}_API void addCallbackMaskExcept(CallbackMask mask, const std::set<std::string> & blackList);
{{ucbinding}}_API void removeCallbackMask(CallbackMask mask);
{{ucbinding}}_API void removeCallbackMaskExcept(CallbackMask mask, const std::set<std::string> & blackList);
{{ucbinding}}_API SimpleFunctionCallback unresolvedCallback();
{{ucbinding}}_API void setUnresolvedCallback(SimpleFunctionCallback callback);
{{ucbinding}}_API FunctionCallback beforeCallback();
{{ucbinding}}_API void setBeforeCallback(FunctionCallback callback);
{{ucbinding}}_API FunctionCallback afterCallback();
{{ucbinding}}_API void setAfterCallback(FunctionCallback callback);
{{ucbinding}}_API FunctionLogCallback logCallback();
{{ucbinding}}_API void setLogCallback(FunctionLogCallback callback);


} // namespace {{binding}}
