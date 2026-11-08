
def calculate_equal_split(total_amount, members, leader_index):
    number_of_members = len(members)

    if number_of_members == 0:
        raise ValueError("Group must have at least one member")

    if total_amount <= 0:
        raise ValueError("Total amount must be greater than zero")

    if leader_index < 0 or leader_index >= number_of_members:
        raise ValueError("Invalid leader index")

    base_share = total_amount // number_of_members

    shares = []

    for i in range(number_of_members):
        shares.append(base_share)

    remainder = total_amount - sum(shares)

    shares[leader_index] += remainder

    return shares

def calculate_percentage_split(total_amount, members, percentages, leader_index):
    number_of_members = len(members)

    if number_of_members == 0:
        raise ValueError("Group must have at least one member")

    if total_amount <= 0:
        raise ValueError("Total amount must be greater than zero")

    if len(members) != len(percentages):
        raise ValueError("Member count and percentage count must match")

    if sum(percentages) != 100:
        raise ValueError("Total percentage must equal 100")

    if leader_index < 0 or leader_index >= number_of_members:
        raise ValueError("Invalid leader index")

    shares = []

    for i in range(number_of_members):
        base_share = total_amount * percentages[i] // 100
        shares.append(base_share)

    remainder = total_amount - sum(shares)

    shares[leader_index] += remainder

    return shares

def calculate_fixed_split(total_amount, members, fixed_amounts):
    number_of_members = len(members)

    if number_of_members == 0:
        raise ValueError("Group must have at least one member")

    if total_amount <= 0:
        raise ValueError("Total amount must be greater than zero")

    if len(members) != len(fixed_amounts):
        raise ValueError("Member count and fixed amount count must match")

    for amount in fixed_amounts:
        if not isinstance(amount, int) or isinstance(amount, bool):
            raise ValueError("Each fixed amount must be an integer")

        if amount < 0:
            raise ValueError("Fixed amount cannot be negative")

    if sum(fixed_amounts) != total_amount:
        raise ValueError("Fixed amounts must equal total amount")

    return fixed_amounts.copy()
