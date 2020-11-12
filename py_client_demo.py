from python_graphql_client import GraphqlClient
import asyncio
import datetime

url = "https://api.digitransit.fi/routing/v1/routers/hsl/index/graphql"

def create_client():
	# Instantiate the client with an endpoint.
	client = GraphqlClient(endpoint=url)

	return client

def parse_data (data):

	parsed_data = {}
	bus_lines = {}

	graph_data = data.get("data", None)

	if graph_data is not None:
		stop_data = graph_data.get("stop", None)

		if stop_data is not None:

			parsed_data["stop_name"] = stop_data.get("name", "")
			parsed_data["stop_code"] = stop_data.get("code", "")

			bus_lines = stop_data.get("routes", None)

			route_data = stop_data.get("stoptimesWithoutPatterns", None)
			#print(route_data)

			if route_data is not None:

				routes = []
				for route in route_data:
					route_dict = {}
					arrival = route.get("realtimeArrival", None)

					if arrival == None:
						arrival = route.get("scheduledArrival", 0)

					route_dict["arrival"] = str(datetime.timedelta(seconds=arrival))
					
					route_dict["destination"] = route.get("headsign", "")

					if route_dict["destination"] != "":
						for bus in bus_lines:
							patterns = bus.get("patterns", None)
							line = bus.get("shortName", None)

							if line is None:
								continue

							if patterns is None:
								continue

							for pattern in patterns:
								headsign = pattern.get("headsign", "")
								if headsign != "":
									if headsign.lower() in route_dict["destination"].lower():
										route_dict["route"] = line

					routes.append(route_dict)

				parsed_data["routes"] = routes
		else:
			print(f"Invalid GTFS Id")
			return

	print(f"Parsed data\n{parsed_data}")
	#print(f"Bus Lines\n{bus_lines}")


def run_query(gtfs_id):
	
	g_client = create_client()

	# Create the query string and variables required for the request.
	query = """
	    query ($id: String!, $sec_left_in_day: Int!) {
			stop (id: $id) {
				name
				code
				routes {
			  		shortName
			  		patterns {
						headsign
			  		}
				}
				stoptimesWithoutPatterns (numberOfDepartures: 500, timeRange: $sec_left_in_day){
					scheduledArrival
		  			realtimeArrival
		  			arrivalDelay
		  			scheduledDeparture
		  			realtimeDeparture
		  			departureDelay
		  			realtime
		  			realtimeState
		  			serviceDay
					headsign
				}
			}
		}
	"""

	now = datetime.datetime.now()
	secs_passed = (now - now.replace(hour=0, minute=0, second=0, microsecond=0)).total_seconds()
	sec_left_in_day = (24*60*60) - secs_passed
	print(sec_left_in_day)

	variables = {"id": gtfs_id.upper(), "sec_left_in_day": int(sec_left_in_day)}

	# Asynchronous request
	data = asyncio.run(g_client.execute_async(query=query, variables=variables))

	parse_data(data)


def main():
	#gtfs_id = "HSL:2143202"
	gtfs_id = "HSL:1140447"
	#gtfs_id = "123456"
	run_query(gtfs_id)

if __name__ == "__main__":
	main()





