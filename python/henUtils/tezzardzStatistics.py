import numpy as np
from queryUtils import *
from plotUtils import *

# Exclude the last day from most of the plots?
exclude_last_day = False

# Set the path to the directory where the transaction information will be saved
# to avoid to query for it again and again
transactions_dir = "../data/transactions"

# Set the path to the directory where the figures will be saved
figures_dir = "../figures"

# Read the connected wallets information (wallets connected to the same user)
connected_wallets = read_json_file("../data/connected_wallets.json")

# Get the complete list of objkt.com bid, ask, english auction and dutch auction
# transactions
bid_transactions = get_all_transactions("bid", transactions_dir, sleep_time=1)
ask_transactions = get_all_transactions("ask", transactions_dir, sleep_time=1)
english_auction_transactions = get_all_transactions(
    "english_auction", transactions_dir, sleep_time=1)
dutch_auction_transactions = get_all_transactions(
    "dutch_auction", transactions_dir, sleep_time=1)

# Get the objkt.com bigmaps
bids_bigmap = get_objktcom_bigmap(
    "bids", "tezzardz", transactions_dir, sleep_time=1)
asks_bigmap = get_objktcom_bigmap(
    "asks", "tezzardz", transactions_dir, sleep_time=1)
english_auctions_bigmap = get_objktcom_bigmap(
    "english auctions", "tezzardz", transactions_dir, sleep_time=1)
dutch_auctions_bigmap = get_objktcom_bigmap(
    "dutch auctions", "tezzardz", transactions_dir, sleep_time=1)

# Select only the bids and asks transactions related with Tezzardz
bid_transactions = [transaction for transaction in bid_transactions if 
                    transaction["parameter"]["value"] in bids_bigmap]
ask_transactions = [transaction for transaction in ask_transactions if 
                    transaction["parameter"]["value"] in asks_bigmap]
english_auction_transactions = [
    transaction for transaction in english_auction_transactions if 
    transaction["parameter"]["value"] in english_auctions_bigmap]
dutch_auction_transactions = [
    transaction for transaction in dutch_auction_transactions if 
    transaction["parameter"]["value"] in dutch_auctions_bigmap]

# Get only the english auction transactions that resulted in a successful sell
english_auction_transactions = [
    transaction for transaction in english_auction_transactions if 
    english_auctions_bigmap[transaction["parameter"]["value"]]["current_price"] != "0"]

# Get the H=N registries bigmap
registries_bigmap = get_hen_bigmap("registries", transactions_dir, sleep_time=1)

# Plot the number of operations per day
plot_operations_per_day(
    bid_transactions, "objkt.com bid operations per day",
    "Days since first minted OBJKT (1st of March)", "Bid operations per day",
    exclude_last_day=exclude_last_day)
save_figure(os.path.join(figures_dir, "bid_operations_per_day.png"))

plot_operations_per_day(
    ask_transactions, "objkt.com ask operations per day",
    "Days since first minted OBJKT (1st of March)", "Ask operations per day",
    exclude_last_day=exclude_last_day)
save_figure(os.path.join(figures_dir, "ask_operations_per_day.png"))

plot_operations_per_day(
    english_auction_transactions, "objkt.com english auction operations per day",
    "Days since first minted OBJKT (1st of March)",
    "English auction operations per day", exclude_last_day=exclude_last_day)
save_figure(os.path.join(figures_dir, "english_auction_operations_per_day.png"))

plot_operations_per_day(
    dutch_auction_transactions, "objkt.com dutch auction operations per day",
    "Days since first minted OBJKT (1st of March)",
    "Dutch auction operations per day", exclude_last_day=exclude_last_day)
save_figure(os.path.join(figures_dir, "dutch_auction_operations_per_day.png"))

# Extract the collector accounts
collectors = extract_objktcom_collector_accounts(
    bid_transactions, ask_transactions, english_auction_transactions,
    dutch_auction_transactions, bids_bigmap, english_auctions_bigmap,
    registries_bigmap)

# Get the list of H=N reported users and add some extra ones that are suspect
# of buying their own OBJKTs with the only purpose to get the free hDAOs
reported_users = get_reported_users()
reported_users.append("tz1eee5rapGDbq2bcZYTQwNbrkB4jVSQSSHx")
reported_users.append("tz1Uby674S4xEw8w7iuM3GEkWZ3fHeHjT696")
reported_users.append("tz1bhMc5uPJynkrHpw7pAiBt6YMhQktn7owF")

# Add the reported users information
add_reported_users_information(collectors, reported_users)

# Print some information about the total number of users
print("There are currently %i unique tezzardsz collectors." % len(collectors))

# Get the total money spent by non-reported collectors
wallet_ids = np.array([wallet_id for wallet_id in collectors])
aliases = np.array([collector["alias"] for collector in collectors.values()])
total_money_spent = np.array(
    [collector["total_money_spent"] for collector in collectors.values()])
is_reported_collector = np.array(
    [collector["reported"] for collector in collectors.values()])
wallet_ids = wallet_ids[~is_reported_collector]
aliases = aliases[~is_reported_collector]
total_money_spent = total_money_spent[~is_reported_collector]

# Combine those wallets that are connected to the same user
is_secondary_wallet = np.full(wallet_ids.shape, False)

for main_wallet_id, secondary_wallet_ids in connected_wallets.items():
    main_wallet_index = np.where(wallet_ids == main_wallet_id)[0]

    if len(main_wallet_index) == 1:
        for secondary_wallet_id in secondary_wallet_ids:
            secondary_wallet_index = np.where(
                wallet_ids == secondary_wallet_id)[0]

            if len(secondary_wallet_index) == 1:
                total_money_spent[main_wallet_index] += total_money_spent[
                    secondary_wallet_index]
                is_secondary_wallet[secondary_wallet_index] = True

wallet_ids = wallet_ids[~is_secondary_wallet]
aliases = aliases[~is_secondary_wallet]
total_money_spent = total_money_spent[~is_secondary_wallet]

# Plot a histogram of the collectors that spent more than 100tez
plot_histogram(
    total_money_spent[total_money_spent >= 0],
    title="Collectors distribution",
    x_label="Total money spent (tez)", y_label="Number of collectors", bins=100)
save_figure(os.path.join(figures_dir, "tezzardz_top_collectors_histogram.png"))

# Order the collectors by the money that they spent
sorted_indices = np.argsort(total_money_spent)[::-1]
wallet_ids = wallet_ids[sorted_indices]
aliases = aliases[sorted_indices]
total_money_spent = total_money_spent[sorted_indices]
collectors_ranking = []

for i in range(len(wallet_ids)):
    collectors_ranking.append({
            "ranking": i + 1,
            "wallet_id": wallet_ids[i],
            "alias": aliases[i],
            "total_money_spent": total_money_spent[i]
        })

print("Non-reported collectors spent a total of %.0f tez." % np.sum(total_money_spent))

for i in [10, 100, 200, 300, 500]:
    print("%.1f%% of that was spent by the top %i collectors." % (
        100 * np.sum(total_money_spent[:i]) / np.sum(total_money_spent), i))

# Print the list of the top 100 collectors
print("\n This is the list of the top 100 collectors:\n")

for i, collector in enumerate(collectors_ranking[:100]):
    if collector["alias"] != "":
        print(" %3i: Collector %s spent %5.0f tez (%s)" % (
            i + 1, collector["wallet_id"], collector["total_money_spent"], collector["alias"]))
    else:
        print(" %3i: Collector %s spent %5.0f tez" % (
            i + 1, collector["wallet_id"], collector["total_money_spent"]))

# Save the collectors ranking list in a json file
save_json_file("tezzardz_collectors_ranking.json", collectors_ranking)
