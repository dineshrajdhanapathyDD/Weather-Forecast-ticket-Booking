#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { WeatherWiseStack } from '../lib/weather-wise-stack';

const app = new cdk.App();

new WeatherWiseStack(app, 'WeatherWiseStack', {
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION,
  },
  description: 'Weather-Wise Flight Booking Agent Infrastructure',
});

app.synth();
