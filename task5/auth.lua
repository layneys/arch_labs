local token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsImV4cCI6MTc0NzI0NTYwNn0.1z1aITKJDnsQ0JEKYG9s6sXlBQmk3okargYNNrlK8B8"

request = function()
    local headers = {}
    headers["Authorization"] = "Bearer " .. token
    return wrk.format("GET", "/users/1", headers)
end

