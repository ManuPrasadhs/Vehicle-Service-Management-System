-- ==================================================
-- DATABASE: Vehicle Service Management System
-- ==================================================

DROP DATABASE IF EXISTS VehicleServiceManagement;
CREATE DATABASE VehicleServiceManagement;
USE VehicleServiceManagement;

-- ==================================================
-- TABLES
-- ==================================================

CREATE TABLE Customer (
    Customer_ID INT PRIMARY KEY,
    Name VARCHAR(50) NOT NULL,
    Address VARCHAR(100),
    Phone_No VARCHAR(15)
);

CREATE TABLE Vehicle (
    Vehicle_ID INT PRIMARY KEY,
    Reg_No VARCHAR(20) UNIQUE NOT NULL,
    Color VARCHAR(30),
    Mileage INT,
    Customer_ID INT,
    FOREIGN KEY (Customer_ID) REFERENCES Customer(Customer_ID)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

CREATE TABLE Mechanic (
    Mechanic_ID INT PRIMARY KEY,
    Name VARCHAR(50) NOT NULL,
    Hire_Date DATE,
    Salary DECIMAL(10,2),
    Phone_Number VARCHAR(15)
);

CREATE TABLE Spare_Parts (
    Part_ID INT PRIMARY KEY,
    Part_Name VARCHAR(50) NOT NULL,
    Manufacturer VARCHAR(50),
    Unit_Price DECIMAL(10,2),
    Quantity_In_Stock INT
);

CREATE TABLE Service_Record (
    Service_ID INT PRIMARY KEY,
    Vehicle_ID INT,
    Mechanic_ID INT,
    Service_Date DATE,
    Problem VARCHAR(100),
    Total_Cost DECIMAL(10,2),
    Status VARCHAR(30),
    Mileage_At_Service INT,
    Duration INT,
    FOREIGN KEY (Vehicle_ID) REFERENCES Vehicle(Vehicle_ID)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    FOREIGN KEY (Mechanic_ID) REFERENCES Mechanic(Mechanic_ID)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

-- Service_Parts table with computed Total_Part_Cost
CREATE TABLE Service_Parts (
    Service_ID INT,
    Part_ID INT,
    Quantity_Used INT,
    Unit_Price DECIMAL(10,2),
    Total_Part_Cost DECIMAL(10,2) GENERATED ALWAYS AS (Unit_Price * Quantity_Used) STORED,
    PRIMARY KEY (Service_ID, Part_ID),
    FOREIGN KEY (Service_ID) REFERENCES Service_Record(Service_ID)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    FOREIGN KEY (Part_ID) REFERENCES Spare_Parts(Part_ID)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

-- ==================================================
-- FUNCTIONS
-- ==================================================

DELIMITER //
CREATE FUNCTION GetInventoryValue()
RETURNS DECIMAL(10,2)
DETERMINISTIC
BEGIN
    DECLARE total DECIMAL(10,2);
    SELECT SUM(Unit_Price * Quantity_In_Stock) INTO total FROM Spare_Parts;
    RETURN IFNULL(total,0);
END//
DELIMITER ;

DELIMITER //
CREATE FUNCTION GetVehicleServiceCost(vID INT)
RETURNS DECIMAL(10,2)
DETERMINISTIC
BEGIN
    DECLARE total DECIMAL(10,2);
    SELECT SUM(Total_Cost) INTO total FROM Service_Record WHERE Vehicle_ID = vID;
    RETURN IFNULL(total,0);
END//
DELIMITER ;

DELIMITER //
CREATE FUNCTION GetAverageSalary()
RETURNS DECIMAL(10,2)
DETERMINISTIC
BEGIN
    DECLARE avgSal DECIMAL(10,2);
    SELECT AVG(Salary) INTO avgSal FROM Mechanic;
    RETURN IFNULL(avgSal,0);
END//
DELIMITER ;

-- ==================================================
-- TRIGGERS
-- ==================================================

DELIMITER //
CREATE TRIGGER ReduceStockAfterService
AFTER INSERT ON Service_Parts
FOR EACH ROW
BEGIN
    UPDATE Spare_Parts
    SET Quantity_In_Stock = Quantity_In_Stock - NEW.Quantity_Used
    WHERE Part_ID = NEW.Part_ID;
END//
DELIMITER ;

DELIMITER //
CREATE TRIGGER PreventNegativeStock
BEFORE UPDATE ON Spare_Parts
FOR EACH ROW
BEGIN
    IF NEW.Quantity_In_Stock < 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Error: Quantity cannot be negative';
    END IF;
END//
DELIMITER ;

DELIMITER //
CREATE TRIGGER UpdateServiceCost
AFTER INSERT ON Service_Parts
FOR EACH ROW
BEGIN
    UPDATE Service_Record
    SET Total_Cost = IFNULL(Total_Cost,0) + NEW.Total_Part_Cost
    WHERE Service_ID = NEW.Service_ID;
END//
DELIMITER ;

-- ==================================================
-- SAMPLE DATA
-- ==================================================

INSERT INTO Customer VALUES
(1,'Rahul Sharma','Delhi','9876543210'),
(2,'Priya Verma','Mumbai','8765432109'),
(3,'Amit Kumar','Bangalore','7654321098');

INSERT INTO Vehicle VALUES
(1,'DL01AB1234','Red',45000,1),
(2,'MH02XY5678','Black',52000,2),
(3,'KA05MN4321','White',60000,3);

INSERT INTO Mechanic VALUES
(1,'Rakesh Singh','2015-03-15',45000,'9123456780'),
(2,'Vijay Patel','2018-07-22',40000,'9234567891'),
(3,'Anjali Mehra','2012-05-10',55000,'9345678912');

INSERT INTO Spare_Parts VALUES
(1,'Oil Filter','Bosch',500,20),
(2,'Air Filter','Mahindra',300,15),
(3,'Brake Pad','Hero',1200,10),
(4,'Engine Oil','Castrol',800,25);

INSERT INTO Service_Record VALUES
(1,1,1,'2025-01-15','Engine check',0,'Completed',45500,2),
(2,2,2,'2025-02-10','Brake issue',0,'Completed',52500,1),
(3,3,3,'2025-03-12','Oil leakage',0,'In Progress',60500,3);

INSERT INTO Service_Parts (Service_ID, Part_ID, Quantity_Used, Unit_Price) VALUES
(1,1,1,500),
(1,4,1,800),
(2,3,1,1200),
(3,2,2,300);

-- ==================================================
-- RELATIONSHIPS SUMMARY
-- ==================================================
-- Customer (1) --- (M) Vehicle
-- Vehicle (1) --- (M) Service_Record
-- Mechanic (1) --- (M) Service_Record
-- Service_Record (M) --- (N) Spare_Parts (via Service_Parts)
