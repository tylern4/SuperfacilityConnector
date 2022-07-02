module SuperfacilityConnector

using HTTP
using JSON3

base_url = "https://api.nersc.gov/api/v1.2"

function make_get(url::String)
    try
        response = HTTP.get(url)
        return JSON3.read_json_str(String(response.body))
    catch e
        return "Error occurred : $e"
    end
end

function make_post(url::String)
    try
        response = HTTP.post(url)
        return JSON3.read_json_str(String(response.body))
    catch e
        return "Error occurred : $e"
    end
end

function make_delete(url::String)
    try
        response = HTTP.post(url)
        return JSON3.read_json_str(String(response.body))
    catch e
        return "Error occurred : $e"
    end
end


function status(name::String="", notes::Bool=false, outages::Bool=false)
    sub_url::String = "/status"

    if name != ""
        name = string("/", name)
        sub_url = string(sub_url, name)
    end

    full_url::String = string(base_url, sub_url)
    make_get(full_url)
end

function status_planned(name::String="")
    sub_url = "/status/outages/planned"

    if name != ""
        name = string("/", name)
        sub_url = string(sub_url, name)
    end

    full_url::String = string(base_url, sub_url)
    make_get(full_url)
end

function status_outages(name::String="")
    sub_url = "/status/outages"

    if name != ""
        name = string("/", name)
        sub_url = string(sub_url, name)
    end

    full_url::String = string(base_url, sub_url)
    make_get(full_url)
end

function status_notes(name::String="")
    sub_url = "/status/notes"

    if name != ""
        name = string("/", name)
        sub_url = string(sub_url, name)
    end

    full_url::String = string(base_url, sub_url)
    make_get(full_url)
end

end # module
