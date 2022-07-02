module SuperfacilityConnector
export status, status_outages, status_notes, status_planned

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

### 

function status(name::String="")
    sub_url::String = "/status"
    return get_status(sub_url, name)
end

function status_planned(name::String="")
    sub_url::String = "/status/outages/planned"
    return get_status(sub_url, name)
end

function status_outages(name::String="")
    sub_url::String = "/status/outages"
    return get_status(sub_url, name)
end

function status_notes(name::String="")
    sub_url::String = "/status/notes"
    return get_status(sub_url, name)
end

function get_status(sub_url::String="/status", name::String="")
    if name != ""
        name = string("/", name)
        sub_url::String = string(sub_url, name)
    end

    full_url::String = string(base_url, sub_url)
    make_get(full_url)
end

end # module
