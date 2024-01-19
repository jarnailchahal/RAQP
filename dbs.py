import re
from typing import Dict

class Relation: 
    def __init__(self, name, attributes, tuples):
        self.name = name
        self.attributes = attributes
        self.tuples = tuples

    def select(self, condition):
        filtered_tuples = [t for t in self.tuples if eval(condition, dict(zip(self.attributes, t)))]
        return Relation(self.name, self.attributes, filtered_tuples)

    def project(self, attributes):
        attr_indices = [self.attributes.index(attr) for attr in attributes]
        projected_tuples = [[t[i] for i in attr_indices] for t in self.tuples]
        return Relation(self.name, attributes, projected_tuples)

    def join(self, other, condition):
        # Prefix attributes with relation names to avoid conflicts
        self_prefixed_attrs = [f"{self.name}_{attr}" for attr in self.attributes]
        other_prefixed_attrs = [f"{other.name}_{attr}" for attr in other.attributes]
        joined_attributes = self_prefixed_attrs + other_prefixed_attrs

        # Create a lambda function for the join condition
        condition_lambda = lambda t1, t2: eval(condition, dict(zip(joined_attributes, t1 + t2)))

        # Perform the join
        joined_tuples = []
        for t1 in self.tuples:
            for t2 in other.tuples:
                if condition_lambda(t1, t2):
                    joined_tuples.append(t1 + t2)

        return Relation(self.name + " JOIN " + other.name, joined_attributes, joined_tuples)


    def union(self, other):
        # Check if the attributes of both relations are the same
        if self.attributes != other.attributes:
            raise ValueError("Attributes mismatch for union operation")

        # Combine tuples from both relations
        union_tuples = list(set(self.tuples + other.tuples))

        # Return a new relation representing the union
        return Relation(self.name + " UNION " + other.name, self.attributes, union_tuples)

    def difference(self, other):
        # Check if the attributes of both relations are the same
        if self.attributes != other.attributes:
            raise ValueError("Attributes mismatch for difference operation")

        # Remove tuples from self that are also in other
        difference_tuples = [t for t in self.tuples if t not in other.tuples]

        # Return a new relation representing the difference
        return Relation(self.name + " DIFFERENCE " + other.name, self.attributes, difference_tuples)


    def __str__(self):
        return f"{self.name}({', '.join(self.attributes)}) = {{\n" + "\n".join([str(t) for t in self.tuples]) + "\n}"

    
def parse_relation(text):
    match = re.match(r"(\w+) \(([\w, ]+)\) = \{([\w, \n]+)\}", text)
    if match:
        name = match.group(1)
        attributes = match.group(2).split(', ')
        tuples = [tuple(item.split(', ')) for item in match.group(3).split('\n')]
        for i in range(len(tuples)):
            tuples[i] = list(tuples[i])
            if len(tuples[i]) != len(attributes):
                raise ValueError(f"Tuple {tuples[i]} does not have the same number of elements as there are attributes")
            for attr in attributes:
                attr_index = attributes.index(attr)
                try:
                    tuples[i][attr_index] = int(tuples[i][attr_index])
                except ValueError:
                    pass  # attribute is not an integer, leave it as a string
            tuples[i] = tuple(tuples[i])
        return Relation(name, attributes, tuples)
    else:
        raise ValueError("Invalid relation format")

def parse_query(query):
    operations = []
    while query:
        if query.startswith('join'):
            match = re.match(r"join\((.*?), (.*?)\) at (.*?) = (.*?)$", query)
            if match:
                operations.append(('join', (match.group(1), match.group(2), match.group(3), match.group(4))))
                query = ""
            else:
                raise ValueError("Invalid join operation format")
            
        elif query.startswith('union'):
            match = re.match(r"union\((.*?), (.*?)\)", query)
            if match:
                operations.append(('union', (match.group(1), match.group(2))))
                query = ""
            else:
                raise ValueError("Invalid union operation format")
            
        elif query.startswith('difference'):
            match = re.match(r"difference\((.*?), (.*?)\)", query)
            if match:
                operations.append(('difference', (match.group(1), match.group(2))))
                query = ""
            else:
                raise ValueError("Invalid difference operation format")     

        else:
            match = re.match(r"(\w+)\((.*?)\)\((.*?)\)", query)
            if match:
                operations.append((match.group(1), match.group(2)))
                query = match.group(3)
            else:
                return (query, operations)
    if operations[0][0] == 'join':
        return (operations[0][1][0], operations)
    else:
        return ("", operations)
    
    

def execute_query(relation: Dict[str, Relation], query: str) -> Relation:
    relation_name, operations = parse_query(query)
    # print(operations)
    # print(relation_name)
    if relation_name == "":
        current_relation = None
    else:
        current_relation = relation[relation_name]
    
    for op, arg in operations:
        if op == "select":
            current_relation = current_relation.select(arg)
        elif op == "project":
            current_relation = current_relation.project(arg.split(', '))
        elif op == "join":
            join_condition = f"{arg[0]}_{arg[2]} == {arg[1]}_{arg[3]}"
            current_relation = current_relation.join(relation[arg[1]], join_condition)
        elif op == "union":
            current_relation = relation[arg[0]].union(relation[arg[1]])
        elif op == "difference":
            current_relation = relation[arg[0]].difference(relation[arg[1]])

        else:
            raise ValueError("Invalid operation")

    return current_relation



relations = {}

# Ask if you want to enter a table or use the example tables

inputchoice = input("Do you want to create your own tables (inputting 'n' will use sample tables) ? (y/n): ")
if inputchoice.lower() == 'n':
    # EXAMPLE TABLES
    relations['Employees'] = parse_relation("Employees (EID, Name, Age, DID) = {E1, John, 32, D1\nE2, Alice, 28, D2\nE3, Bob, 29, D2}")
    relations['Departments'] = parse_relation("Departments (DID, Name) = {D1, Sales\nD2, Marketing\nD3, Engineering}")
    relations['Table1'] = parse_relation("Table1 (a1, a2) = {1, 2\n3, 4}")
    relations['Table2'] = parse_relation("Table2 (a1, a2) = {1, 2\n5, 6}")

    print("---------------Sample Tables + Values--------------------|")
    print()
    # print all tables 
    for key in relations:
        print(relations[key])
        print()
    print("---------------Sample Tables + Values--------------------|")
    print()

elif inputchoice.lower() == 'y':
    print("---------------Enter Tables--------------------|")
    print()
    while True:
        tablename = input("Enter the table name (or 'e' to exit) (# example input: Employees): ") 
        if tablename.lower() == 'e':
            break

        tableattributes = input("Enter the table attributes (# example input: EID, Name, Age, DID) : ")
        tabletuples = []
        while True:
            row = input("Enter the next row of the table tuples (or 'e' to exit) ((# example input: E1, John, 32, D1)): ")
            if row.lower() == 'e':
                break
            tabletuples.append(row)

        originalinput = tablename + " (" + tableattributes + ") = {"
        if len(tabletuples) == 1:
            originalinput += tabletuples[0] + "}"
        else:
            for i in range(len(tabletuples)):
                if i == len(tabletuples) - 1:
                    originalinput += tabletuples[i]
                else:
                    originalinput += tabletuples[i] + "\n"
            originalinput += "}"

        relation = parse_relation(originalinput)
        relations[tablename] = relation

    print("---------------Inputted Tables + Values--------------------|")
    print()
    # print all tables 
    for key in relations:
        print(relations[key])
        print()
    print("---------------Inputted Tables + Values--------------------|")
    print()



else :
    print("Invalid input. Exiting program.")
    exit()


print("---------------Example Queries--------------------|")
print("select(Age>30)(Employees)")
print("select(DID == 'D1')(Departments)")
print("project(Name, Age)(Employees)")
print("join(Employees, Departments) at DID = DID")
print("union(Table1, Table2)")
print("difference(Table1, Table2)")
print("difference(Table2, Table1)")
print("---------------Example Queries--------------------|")

# keep asking for queries until user enters 'e'

while True:
    print()
    query = input("Please enter a query : ")

    if query.lower() == 'e':
        break

    result = execute_query(relations, query)

    print("---------------Query Result--------------------|")
    print(result)
    print("---------------Query Result--------------------|")
    print()



# EXAMPLE QUERIES
# query = "select(Age>30)(Employees)"
# or
# query = "select(DID == 'D1')(Departments)"
# or
# query = "project(Name, Age)(Employees)"
# or
# query = "join(Employees, Departments) at DID = DID"
# or
# query = "union(Table1, Table2)"
# or
# query = "difference(Table1, Table2)"
# or
# query = "difference(Table2, Table1)"


