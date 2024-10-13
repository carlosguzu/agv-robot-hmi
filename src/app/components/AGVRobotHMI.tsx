"use client";

import React, { useState, useEffect } from 'react'
import { io, Socket } from 'socket.io-client'
import { Joystick } from 'react-joystick-component'
import { Battery, Gauge } from 'lucide-react'

import { Card, CardContent, CardHeader, CardTitle } from "./ui/card"
import { Slider } from "./ui/slider"
import { Button } from "./ui/button"

// Definimos nuestra propia interfaz para el evento del joystick
interface IJoystickUpdateEvent {
  type: 'move' | 'stop' | 'start'
  x: number
  y: number
  direction: { 
    angle: { 
      degree: number 
    } 
  }
  distance: number
}

const socket: Socket = io()

export default function AGVRobotHMI() {
  const [steer, setSteer] = useState<number>(50)
  const [speed, setSpeed] = useState<number>(50)
  const [voltage, setVoltage] = useState<number>(42)
  const [isConnected, setIsConnected] = useState<boolean>(false)

  useEffect(() => {
    socket.on('connect', () => setIsConnected(true))
    socket.on('disconnect', () => setIsConnected(false))
    socket.on('voltage', (value: number) => setVoltage(value))

    return () => {
      socket.off('connect')
      socket.off('disconnect')
      socket.off('voltage')
    }
  }, [])

  const handleJoystickMove = (event: IJoystickUpdateEvent) => {
    const angle = event.direction.angle.degree
    const distance = event.distance

    const limitedDistance = Math.min(distance, 100)
    const newSpeed = Math.round(limitedDistance * Math.sin(angle * (Math.PI / 180)) * (speed / 100) * 10)
    const newSteer = Math.round(limitedDistance * Math.cos(angle * (Math.PI / 180)) * (steer / 100) * 10)

    sendControl(newSteer, newSpeed)
  }

  const handleJoystickStop = () => {
    sendControl(0, 0)
  }

  const sendControl = (steerValue: number, speedValue: number) => {
    socket.emit('control', { steer: steerValue, speed: speedValue, SliderX: steer, SliderY: speed })
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-100 to-gray-200 p-8">
      <h1 className="text-4xl font-bold text-center mb-8 text-gray-800">HMI de Robot Móvil Guiado</h1>
      
      <div className="max-w-4xl mx-auto grid grid-cols-1 md:grid-cols-2 gap-8">
        <Card>
          <CardHeader>
            <CardTitle>Video en Vivo</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="aspect-video bg-black rounded-lg overflow-hidden">
              <img src="/video_feed" alt="Video en Vivo" className="w-full h-full object-cover" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Controles</CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="flex justify-center">
              <Joystick 
                size={150} 
                baseColor="#e2e8f0" 
                stickColor="#3b82f6" 
                // throttle={100}
                // move={handleJoystickMove} 
                stop={handleJoystickStop}
              />
            </div>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">% Steer</label>
                <Slider
                  value={[steer]}
                  onValueChange={(value) => {
                    setSteer(value[0])
                    sendControl(value[0], speed)
                  }}
                  max={100}
                  step={1}
                />
                <span className="text-sm text-gray-500">{steer}%</span>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">% Speed</label>
                <Slider
                  value={[speed]}
                  onValueChange={(value) => {
                    setSpeed(value[0])
                    sendControl(steer, value[0])
                  }}
                  max={100}
                  step={1}
                />
                <span className="text-sm text-gray-500">{speed}%</span>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Estado del Sistema</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center space-x-2">
              <Battery className={`h-6 w-6 ${voltage > 30 ? 'text-green-500' : 'text-red-500'}`} />
              <span className="text-lg font-semibold">{voltage}V</span>
            </div>
            <div className="flex items-center space-x-2">
              <Gauge className={`h-6 w-6 ${isConnected ? 'text-green-500' : 'text-red-500'}`} />
              <span className="text-lg font-semibold">{isConnected ? 'Conectado' : 'Desconectado'}</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Acciones Rápidas</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <Button className="w-full" onClick={() => sendControl(0, 0)}>Parada de Emergencia</Button>
            <Button className="w-full" onClick={() => {
              setSteer(50)
              setSpeed(50)
              sendControl(50, 50) 
            }}>Reiniciar Controles</Button>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}