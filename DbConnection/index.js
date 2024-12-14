import mongoose from "mongoose";



 export const connectDb = async()=>{
    try {
        const connection = mongoose.connect('mongodb+srv://sujal1234:sujal123456@cluster0.l6lil.mongodb.net/', { useNewUrlParser: true, useUnifiedTopology: true, serverSelectionTimeoutMS: 30000 });
        console.log('MongoDB Connected...');
    } catch (error) {
        console.log('mongoDB connection failed',error);
        
    }
}