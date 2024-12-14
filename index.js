import express from 'express';
import { MongoClient } from 'mongodb';
import mongoose from 'mongoose';
import bodyParser from 'body-parser';
import cors from 'cors'


const app = express();
const port = 3000;


const uri = 'mongodb+srv://sujal1234:sujal123456@cluster0.l6lil.mongodb.net/';
const databaseName = "CarPlateDB"; 
const collectionName = "ParkingStatus";
const entryCollection = "CarPlateData"
const exitcollection= "CarExit"

let db, collection;
app.use(cors())
app.use(express.json()); // Added to handle JSON payloads
app.use(bodyParser.urlencoded({ extended: true }))

MongoClient.connect(uri, { useNewUrlParser: true, useUnifiedTopology: true })
  .then(client => {
    console.log('Connected to MongoDB');
    db = client.db(databaseName);
    collection = db.collection(collectionName);

    app.listen(port, () => {
      console.log(`Server is running on http://localhost:${port}`);
    });

    setInterval(async () => {
      try {
        const data = await collection.findOne({}, { sort: { timestamp: -1 } }); 
        console.log('Real-time Data:', data);
      } catch (err) {
        console.error('Error fetching data:', err);
      }
    }, 1000);
  })
  .catch(err => console.error('Error connecting to MongoDB:', err));
  
   app.use(bodyParser.json());

 
   const userSchema = new mongoose.Schema({
    username: String,
    password: String,
    numberPlate: String,
    userType: String,
   });
   
   const User = mongoose.model('User', userSchema);
   
 
   app.post('/signup', async (req, res) => {
     const { username, password, numberPlate, userType } = req.body;
     if(!username || !password || !numberPlate ||!userType){
      return res.status(400).json({ message: 'Please fill in all fields.' });
     }
   
     try {
       const newUser = User.create({
         username,
         password,
         numberPlate,
         userType,
       });
       
   
       if(!newUser){
        res.status(401).send({ message: 'Error registering user', error });
       }
       res.status(201).send({ message: 'User registered successfully!' });
     } catch (error) {
       console.error('Error saving user data', error);
       res.status(500).send({ message: 'Error registering user', error });
     }
   });
   app.post('/signin', async (req, res) => {
    const { username, password } = req.body;
  
    // Validate input
    if (!username || !password) {
      return res.status(400).json({ message: 'Please provide username and password.' });
    }
  
    try {
      // Find user by username
      const user = await User.findOne({ username });
  
      if (!user) {
        return res.status(401).json({ message: 'Invalid username or password.' });
      }
  
      // Compare passwords (if passwords are hashed, use bcrypt.compare)
      
  
      if(password!=user.password) {
        return res.status(401).json({ message: 'Invalid username or password.' });
      }
  
      // Send success response
      res.status(200).json({ message: 'Login successful', user: { username: user.username, userType: user.userType, numberPlate: user.numberPlate } });
    } catch (error) {
      console.error('Error during login:', error);
      res.status(500).json({ message: 'An error occurred during login.' });
    }
  });
   



app.get('/parking-data', async (req, res) => {
  try {
    const data = await collection.findOne({}, { sort: { timestamp: -1 } });
    res.json(data);
  } catch (err) {
    res.status(500).json({ error: 'Error fetching data' });
  }
});


app.get('/parking-slots/:role', async (req, res) => {
  try {
    const role = req.params.role;
    const data = await collection.findOne({}, { sort: { timestamp: -1 } });

    let slots = role === 'VIP' ? data.vip_slots : data.common_slots;
    res.json(slots);
  } catch (err) {
    res.status(500).json({ error: 'Error fetching data' });
  }
});

