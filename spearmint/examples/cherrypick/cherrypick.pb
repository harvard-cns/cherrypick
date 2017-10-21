language: PYTHON
name: "cherrypick_offline"

variable {
    name: "cpu_type"
    type: ENUM
    size: 1
    options: "fast"
    options: "slow"
}

variable {
    name: "cpu_count"
    type: INT
    size: 1
    min: 2
    max: 8
}

variable {
    name: "machine_count"
    type: INT
    size: 1
    min: 2
    max: 7
}

variable {
    name: "disk_type"
    type: ENUM
    size: 1
    options: "fast"
    options: "slow"
}

variable {
    name: "ram"
    type: ENUM
    size: 1
    options: "low"
    options: "medium"
    options: "high"
}
